"""ICU MessageFormat formatters for placeholders, plurals, and select."""

import re
from functools import lru_cache
from typing import Any

from .exceptions import ICUFormatError
from .plural_rules import get_plural_category, PluralCategory


class PlaceholderFormatter:
    """Formats simple placeholder substitution: {name}, {count}, etc."""

    @staticmethod
    def format(template: str, **kwargs: Any) -> str:
        """Replace placeholders in template with provided values.

        Args:
            template: Template string with {placeholder} syntax
            **kwargs: Values for placeholders

        Returns:
            Formatted string

        Examples:
            >>> PlaceholderFormatter.format("Hello, {name}!", name="World")
            "Hello, World!"
        """
        try:
            # Simple string format for basic placeholders
            return template.format(**kwargs)
        except KeyError as e:
            raise ICUFormatError(template, f"Missing placeholder value: {e}")
        except ValueError as e:
            raise ICUFormatError(template, f"Invalid format: {e}")


class PluralFormatter:
    """Formats ICU plural patterns: {count, plural, =0{...} one{...} other{...}}"""

    def __init__(self, locale: str = "en"):
        """Initialize plural formatter.

        Args:
            locale: Locale code for plural rules
        """
        self.locale = locale

    def format(self, template: str, **kwargs: Any) -> str:
        """Format template with plural rules.

        Args:
            template: Template with ICU plural syntax
            **kwargs: Values including the number for plural selection

        Returns:
            Formatted string

        Examples:
            >>> formatter = PluralFormatter("en")
            >>> formatter.format("{count, plural, =0{No items} one{One item} other{{count} items}}", count=0)
            "No items"
            >>> formatter.format("{count, plural, =0{No items} one{One item} other{{count} items}}", count=1)
            "One item"
            >>> formatter.format("{count, plural, =0{No items} one{One item} other{{count} items}}", count=5)
            "5 items"
        """
        # Find all plural patterns
        pattern = self._parse_plural_pattern(template)
        if not pattern:
            # No plural pattern, just do simple formatting
            return PlaceholderFormatter.format(template, **kwargs)

        var_name, cases = pattern

        # Get the number value
        if var_name not in kwargs:
            raise ICUFormatError(
                template, f"Missing value for plural variable '{var_name}'"
            )

        number = kwargs[var_name]
        if not isinstance(number, (int, float)):
            raise ICUFormatError(
                template,
                f"Plural variable '{var_name}' must be a number, got {type(number).__name__}",
            )

        # Select the appropriate case
        selected_template = self._select_plural_case(number, cases)

        # Replace the plural pattern with the selected template
        result = self._replace_plural_pattern(template, selected_template)

        # Format remaining placeholders
        return PlaceholderFormatter.format(result, **kwargs)

    def _parse_plural_pattern(self, template: str) -> tuple[str, dict[str, str]] | None:
        """Parse ICU plural pattern from template.

        Returns:
            Tuple of (variable_name, cases_dict) or None if no plural pattern found
        """
        # Find the pattern manually to handle nested braces
        pattern_start = template.find("{")
        if pattern_start == -1:
            return None

        # Check if it's a plural pattern
        comma_pos = template.find(",", pattern_start)
        if comma_pos == -1:
            return None

        plural_pos = template.find("plural", comma_pos)
        if plural_pos == -1 or plural_pos > comma_pos + 20:
            return None

        # Extract variable name
        var_name = template[pattern_start + 1 : comma_pos].strip()

        # Find the matching closing brace by counting braces
        brace_count = 1
        i = plural_pos + 6  # Skip 'plural'

        # Skip whitespace and comma after 'plural'
        while i < len(template) and template[i] in ", \t\n":
            i += 1

        cases_start = i

        while i < len(template) and brace_count > 0:
            if template[i] == "{":
                brace_count += 1
            elif template[i] == "}":
                brace_count -= 1
            i += 1

        if brace_count != 0:
            return None

        cases_str = template[cases_start : i - 1]  # Exclude final }

        # Parse cases: =0{...} one{...} other{...}
        cases = self._parse_cases(cases_str)

        return var_name, cases

    def _parse_cases(self, cases_str: str) -> dict[str, str]:
        """Parse plural cases from ICU syntax.

        Args:
            cases_str: String like "=0{No items} one{One item} other{{count} items}"

        Returns:
            Dictionary mapping case names to their templates
        """
        cases = {}

        # Pattern to match cases: =N{...} or word{...}
        # This regex handles nested braces
        i = 0
        while i < len(cases_str):
            # Skip whitespace
            while i < len(cases_str) and cases_str[i].isspace():
                i += 1

            if i >= len(cases_str):
                break

            # Extract case name (=0, one, few, other, etc.)
            case_start = i
            while (
                i < len(cases_str)
                and cases_str[i] not in "{"
                and not cases_str[i].isspace()
            ):
                i += 1

            case_name = cases_str[case_start:i].strip()

            if not case_name:
                break

            # Skip whitespace before {
            while i < len(cases_str) and cases_str[i].isspace():
                i += 1

            if i >= len(cases_str) or cases_str[i] != "{":
                break

            # Extract case template (handle nested braces)
            i += 1  # Skip opening {
            brace_count = 1
            template_start = i

            while i < len(cases_str) and brace_count > 0:
                if cases_str[i] == "{":
                    brace_count += 1
                elif cases_str[i] == "}":
                    brace_count -= 1
                i += 1

            template = cases_str[template_start : i - 1]  # Exclude closing }
            cases[case_name] = template

        return cases

    def _select_plural_case(self, number: int | float, cases: dict[str, str]) -> str:
        """Select the appropriate plural case for a number.

        Args:
            number: The number to pluralize
            cases: Dictionary of plural cases

        Returns:
            Selected template string
        """
        # Try exact match first (=0, =1, etc.)
        exact_key = f"={int(number)}"
        if exact_key in cases:
            return cases[exact_key]

        # Get CLDR plural category
        category = get_plural_category(self.locale, number)

        # Try the category
        if category in cases:
            return cases[category]

        # Fall back to "other" (required in ICU)
        if "other" in cases:
            return cases["other"]

        # If no "other" case, use any available case
        if cases:
            return next(iter(cases.values()))

        return str(number)

    def _replace_plural_pattern(self, template: str, replacement: str) -> str:
        """Replace the plural pattern in template with the selected case.

        Args:
            template: Original template with plural pattern
            replacement: Selected case template

        Returns:
            Template with plural pattern replaced
        """
        # Find the first plural pattern manually to handle nested braces
        pattern_start = template.find("{")
        if pattern_start == -1:
            return template

        # Check if it contains 'plural'
        comma_pos = template.find(",", pattern_start)
        if comma_pos == -1:
            return template

        plural_pos = template.find("plural", comma_pos)
        if plural_pos == -1:
            return template

        # Find the matching closing brace by counting
        brace_count = 1
        i = pattern_start + 1

        while i < len(template) and brace_count > 0:
            if template[i] == "{":
                brace_count += 1
            elif template[i] == "}":
                brace_count -= 1
            i += 1

        if brace_count != 0:
            return template

        # Replace the entire plural pattern with the replacement
        return template[:pattern_start] + replacement + template[i:]


class SelectFormatter:
    """Formats ICU select patterns: {gender, select, male{...} female{...} other{...}}"""

    @staticmethod
    def format(template: str, **kwargs: Any) -> str:
        """Format template with select (choice) rules.

        Args:
            template: Template with ICU select syntax
            **kwargs: Values including the choice variable

        Returns:
            Formatted string

        Examples:
            >>> SelectFormatter.format("{gender, select, male{He} female{She} other{They}}", gender="male")
            "He"
            >>> SelectFormatter.format("{gender, select, male{He} female{She} other{They}}", gender="female")
            "She"
        """
        # Find all select patterns
        pattern = SelectFormatter._parse_select_pattern(template)
        if not pattern:
            # No select pattern, just do simple formatting
            return PlaceholderFormatter.format(template, **kwargs)

        var_name, cases = pattern

        # Get the choice value
        if var_name not in kwargs:
            raise ICUFormatError(
                template, f"Missing value for select variable '{var_name}'"
            )

        choice = str(kwargs[var_name])

        # Select the appropriate case
        selected_template = cases.get(choice, cases.get("other", ""))

        # Replace the select pattern with the selected template
        result = SelectFormatter._replace_select_pattern(template, selected_template)

        # Format remaining placeholders
        return PlaceholderFormatter.format(result, **kwargs)

    @staticmethod
    def _parse_select_pattern(template: str) -> tuple[str, dict[str, str]] | None:
        """Parse ICU select pattern from template.

        Returns:
            Tuple of (variable_name, cases_dict) or None if no select pattern found
        """
        # Match: {varName, select, cases...}
        match = re.search(r"\{(\w+)\s*,\s*select\s*,\s*([^}]+)\}", template, re.DOTALL)
        if not match:
            return None

        var_name = match.group(1)
        cases_str = match.group(2)

        # Parse cases (same format as plural)
        cases = PluralFormatter()._parse_cases(cases_str)

        return var_name, cases

    @staticmethod
    def _replace_select_pattern(template: str, replacement: str) -> str:
        """Replace the select pattern in template with the selected case.

        Args:
            template: Original template with select pattern
            replacement: Selected case template

        Returns:
            Template with select pattern replaced
        """
        # Replace the first select pattern
        return re.sub(
            r"\{\w+\s*,\s*select\s*,\s*[^}]+\}",
            replacement,
            template,
            count=1,
            flags=re.DOTALL,
        )


class MessageFormatter:
    """Main formatter that handles all ICU MessageFormat patterns."""

    def __init__(self, locale: str = "en"):
        """Initialize message formatter.

        Args:
            locale: Locale code for locale-specific formatting
        """
        self.locale = locale
        self.plural_formatter = PluralFormatter(locale)

    @lru_cache(maxsize=256)
    def compile(self, pattern: str) -> "CompiledPattern":
        """Compile an ICU MessageFormat pattern for faster repeated use.

        Args:
            pattern: ICU MessageFormat pattern string

        Returns:
            CompiledPattern object
        """
        return CompiledPattern(pattern, self.locale)

    def format(self, pattern: str, **kwargs: Any) -> str:
        """Format a message with all ICU features.

        Args:
            pattern: ICU MessageFormat pattern
            **kwargs: Values for placeholders

        Returns:
            Formatted string
        """
        compiled = self.compile(pattern)
        return compiled.format(**kwargs)


class CompiledPattern:
    """Compiled ICU MessageFormat pattern for efficient repeated formatting."""

    def __init__(self, pattern: str, locale: str = "en"):
        """Initialize compiled pattern.

        Args:
            pattern: ICU MessageFormat pattern
            locale: Locale code
        """
        self.pattern = pattern
        self.locale = locale
        self.has_plural = "plural" in pattern
        self.has_select = "select" in pattern
        self.plural_formatter = PluralFormatter(locale) if self.has_plural else None

    def format(self, **kwargs: Any) -> str:
        """Format the compiled pattern with provided values.

        Args:
            **kwargs: Values for placeholders

        Returns:
            Formatted string
        """
        result = self.pattern

        # Process select patterns first
        if self.has_select:
            result = SelectFormatter.format(result, **kwargs)

        # Process plural patterns
        if self.has_plural and self.plural_formatter:
            result = self.plural_formatter.format(result, **kwargs)

        # Process remaining simple placeholders
        result = PlaceholderFormatter.format(result, **kwargs)

        return result
