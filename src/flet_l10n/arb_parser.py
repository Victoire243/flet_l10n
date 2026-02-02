"""ARB (Application Resource Bundle) file parser.

Parses JSON-based ARB files used for localization, compatible with Flutter's l10n format.
"""

import json
from pathlib import Path
from typing import Any

from .exceptions import ARBParseError


class ARBEntry:
    """Represents a single translation entry from an ARB file."""

    def __init__(self, key: str, value: str, metadata: dict[str, Any] | None = None):
        """Initialize ARB entry.

        Args:
            key: Translation key
            value: Translation value (can contain ICU MessageFormat syntax)
            metadata: Optional metadata from @key entry
        """
        self.key = key
        self.value = value
        self.metadata = metadata or {}

    @property
    def description(self) -> str | None:
        """Get description from metadata."""
        return self.metadata.get("description")

    @property
    def placeholders(self) -> dict[str, Any]:
        """Get placeholders definition from metadata."""
        return self.metadata.get("placeholders", {})

    @property
    def type(self) -> str:
        """Get type from metadata (e.g., 'text', 'plural', 'select')."""
        return self.metadata.get("type", "text")

    def __repr__(self) -> str:
        return f"ARBEntry(key={self.key!r}, value={self.value!r})"


class ARBParser:
    """Parser for ARB (Application Resource Bundle) files."""

    def __init__(self):
        self._locale: str | None = None
        self._entries: dict[str, ARBEntry] = {}

    def parse_file(self, file_path: Path | str) -> dict[str, ARBEntry]:
        """Parse an ARB file.

        Args:
            file_path: Path to the ARB file

        Returns:
            Dictionary mapping translation keys to ARBEntry objects

        Raises:
            ARBParseError: If file cannot be parsed
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ARBParseError(str(file_path), "File does not exist")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ARBParseError(str(file_path), f"Invalid JSON: {e}")
        except Exception as e:
            raise ARBParseError(str(file_path), f"Error reading file: {e}")

        if not isinstance(data, dict):
            raise ARBParseError(str(file_path), "ARB file must contain a JSON object")

        return self.parse_dict(data, str(file_path))

    def parse_dict(
        self, data: dict[str, Any], source: str = "<dict>"
    ) -> dict[str, ARBEntry]:
        """Parse ARB data from a dictionary.

        Args:
            data: Dictionary containing ARB data
            source: Source identifier for error messages

        Returns:
            Dictionary mapping translation keys to ARBEntry objects

        Raises:
            ARBParseError: If data is invalid
        """
        self._entries = {}
        self._locale = None

        # Extract locale if present
        if "@@locale" in data:
            self._locale = data["@@locale"]
            if not isinstance(self._locale, str):
                raise ARBParseError(source, "@@locale must be a string")

        # Parse entries
        metadata_map: dict[str, dict] = {}

        # First pass: collect metadata entries (keys starting with @)
        for key, value in data.items():
            if key.startswith("@@"):
                # Global metadata like @@locale, @@last_modified
                continue
            elif key.startswith("@"):
                # Entry metadata
                original_key = key[1:]  # Remove @ prefix
                if not isinstance(value, dict):
                    raise ARBParseError(
                        source,
                        f"Metadata for '{original_key}' must be an object, got {type(value).__name__}",
                    )
                metadata_map[original_key] = value

        # Second pass: collect translation entries
        for key, value in data.items():
            if key.startswith("@"):
                # Skip metadata entries
                continue

            if not isinstance(value, str):
                raise ARBParseError(
                    source,
                    f"Translation value for '{key}' must be a string, got {type(value).__name__}",
                )

            metadata = metadata_map.get(key, {})
            self._entries[key] = ARBEntry(key, value, metadata)

        return self._entries

    @property
    def locale(self) -> str | None:
        """Get the locale from the last parsed ARB file."""
        return self._locale

    @property
    def entries(self) -> dict[str, ARBEntry]:
        """Get the entries from the last parsed ARB file."""
        return self._entries

    def validate(self) -> list[str]:
        """Validate the parsed ARB data.

        Returns:
            List of validation warning/error messages (empty if valid)
        """
        warnings = []

        if not self._entries:
            warnings.append("No translation entries found")

        if not self._locale:
            warnings.append("Missing @@locale field")

        # Check for common issues
        for key, entry in self._entries.items():
            # Check for empty values
            if not entry.value.strip():
                warnings.append(f"Empty translation value for key '{key}'")

            # Check for placeholder mismatches
            placeholders_in_value = self._extract_placeholders(entry.value)
            placeholders_in_metadata = set(entry.placeholders.keys())

            # Placeholders in value but not in metadata
            missing_metadata = placeholders_in_value - placeholders_in_metadata
            if missing_metadata:
                warnings.append(
                    f"Key '{key}': placeholders {missing_metadata} used in value "
                    f"but not defined in metadata"
                )

            # Placeholders in metadata but not used in value
            unused_metadata = placeholders_in_metadata - placeholders_in_value
            if unused_metadata:
                warnings.append(
                    f"Key '{key}': placeholders {unused_metadata} defined in metadata "
                    f"but not used in value"
                )

        return warnings

    @staticmethod
    def _extract_placeholders(text: str) -> set[str]:
        """Extract placeholder names from ICU MessageFormat text.

        Args:
            text: Text potentially containing placeholders like {name} or {count, plural, ...}

        Returns:
            Set of placeholder names
        """
        placeholders = set()
        depth = 0
        current_placeholder = []

        i = 0
        while i < len(text):
            char = text[i]

            if char == "{":
                depth += 1
                if depth == 1:
                    current_placeholder = []
            elif char == "}":
                depth -= 1
                if depth == 0 and current_placeholder:
                    # Extract placeholder name (before first comma or space)
                    name = "".join(current_placeholder).split(",")[0].strip()
                    if name:
                        placeholders.add(name)
                    current_placeholder = []
            elif depth > 0:
                current_placeholder.append(char)

            i += 1

        return placeholders


def extract_locale_from_filename(filename: str) -> str | None:
    """Extract locale code from ARB filename.

    Follows Flutter's naming convention: app_en.arb, intl_es_ES.arb, etc.

    Args:
        filename: ARB filename (e.g., 'app_en.arb', 'intl_es_ES.arb')

    Returns:
        Locale code (e.g., 'en', 'es_ES') or None if not found
    """
    if not filename.endswith(".arb"):
        return None

    # Remove .arb extension
    base = filename[:-4]

    # Split by underscore and take the last part(s) as locale
    parts = base.split("_")

    if len(parts) < 2:
        return None

    # Last part should be locale code (e.g., 'en', 'ES')
    locale_parts = []

    # Work backwards to build locale code
    for part in reversed(parts):
        # Stop if we hit a non-locale part (typically has more than 3 chars)
        if len(part) > 3 and not part.isupper():
            break
        locale_parts.insert(0, part)

    if locale_parts:
        return "_".join(locale_parts)

    return None
