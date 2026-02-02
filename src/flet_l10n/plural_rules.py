"""CLDR plural rules implementation for locale-aware pluralization.

Based on Unicode CLDR plural rules:
https://unicode-org.github.io/cldr-staging/charts/latest/supplemental/language_plural_rules.html
"""

from typing import Literal

PluralCategory = Literal["zero", "one", "two", "few", "many", "other"]


def get_plural_category(locale: str, number: int | float) -> PluralCategory:
    """Get the plural category for a number in a given locale.

    Args:
        locale: Locale code (e.g., 'en', 'es', 'ru', 'ar')
        number: The number to categorize

    Returns:
        One of: 'zero', 'one', 'two', 'few', 'many', 'other'
    """
    # Normalize locale to base language code
    lang = locale.split("-")[0].split("_")[0].lower()

    # Get the rule function for this language
    rule_func = _PLURAL_RULES.get(lang, _rule_other_only)

    return rule_func(number)


# === Plural Rule Implementations ===


def _rule_other_only(n: int | float) -> PluralCategory:
    """Languages with no plural distinction: Chinese, Japanese, Korean, Thai, Vietnamese, etc."""
    return "other"


def _rule_one_other(n: int | float) -> PluralCategory:
    """English, German, Dutch, Swedish, Danish, Norwegian, Finnish, etc."""
    if n == 1:
        return "one"
    return "other"


def _rule_zero_one_other(n: int | float) -> PluralCategory:
    """Latvian, etc."""
    if n == 0:
        return "zero"
    if n == 1:
        return "one"
    return "other"


def _rule_one_two_other(n: int | float) -> PluralCategory:
    """Cornish, etc."""
    if n == 1:
        return "one"
    if n == 2:
        return "two"
    return "other"


def _rule_french(n: int | float) -> PluralCategory:
    """French, Portuguese (Brazil), etc.: 0 and 1 are 'one', others are 'other'."""
    if n == 0 or n == 1:
        return "one"
    return "other"


def _rule_czech_slovak(n: int | float) -> PluralCategory:
    """Czech, Slovak: complex rules for one/few/many/other."""
    if n == 1:
        return "one"
    if 2 <= n <= 4:
        return "few"
    return "other"


def _rule_polish(n: int | float) -> PluralCategory:
    """Polish: complex rules based on last digit."""
    if n == 1:
        return "one"

    # Get last digit and last two digits
    last_digit = int(n) % 10
    last_two = int(n) % 100

    if 2 <= last_digit <= 4 and not (12 <= last_two <= 14):
        return "few"

    return "other"


def _rule_russian(n: int | float) -> PluralCategory:
    """Russian, Ukrainian, Belarusian, Serbian: complex Slavic rules."""
    if n == 0:
        return "other"

    last_digit = int(n) % 10
    last_two = int(n) % 100

    if last_digit == 1 and last_two != 11:
        return "one"

    if 2 <= last_digit <= 4 and not (12 <= last_two <= 14):
        return "few"

    return "many"


def _rule_romanian(n: int | float) -> PluralCategory:
    """Romanian: special rules for few category."""
    if n == 1:
        return "one"

    if n == 0 or (1 < (n % 100) < 20):
        return "few"

    return "other"


def _rule_arabic(n: int | float) -> PluralCategory:
    """Arabic: six-form plural with zero, one, two, few, many, other."""
    if n == 0:
        return "zero"
    if n == 1:
        return "one"
    if n == 2:
        return "two"

    last_two = int(n) % 100

    if 3 <= last_two <= 10:
        return "few"
    if 11 <= last_two <= 99:
        return "many"

    return "other"


def _rule_welsh(n: int | float) -> PluralCategory:
    """Welsh: zero, one, two, few, many, other."""
    if n == 0:
        return "zero"
    if n == 1:
        return "one"
    if n == 2:
        return "two"
    if n == 3:
        return "few"
    if n == 6:
        return "many"
    return "other"


def _rule_irish(n: int | float) -> PluralCategory:
    """Irish: complex rules with multiple categories."""
    if n == 1:
        return "one"
    if n == 2:
        return "two"
    if 3 <= n <= 6:
        return "few"
    if 7 <= n <= 10:
        return "many"
    return "other"


def _rule_maltese(n: int | float) -> PluralCategory:
    """Maltese: complex rules similar to Arabic."""
    if n == 1:
        return "one"
    if n == 0 or (2 <= (n % 100) <= 10):
        return "few"
    if 11 <= (n % 100) <= 19:
        return "many"
    return "other"


def _rule_slovenian(n: int | float) -> PluralCategory:
    """Slovenian: special two, few categories."""
    last_two = int(n) % 100

    if last_two == 1:
        return "one"
    if last_two == 2:
        return "two"
    if last_two in (3, 4):
        return "few"

    return "other"


def _rule_icelandic(n: int | float) -> PluralCategory:
    """Icelandic: special rules for one."""
    last_digit = int(n) % 10
    last_two = int(n) % 100

    if last_digit == 1 and last_two != 11:
        return "one"

    return "other"


# === Language to Rule Mapping ===
# Based on CLDR data - covering the most common languages

_PLURAL_RULES: dict[str, callable] = {
    # No plural distinction
    "zh": _rule_other_only,  # Chinese
    "ja": _rule_other_only,  # Japanese
    "ko": _rule_other_only,  # Korean
    "th": _rule_other_only,  # Thai
    "vi": _rule_other_only,  # Vietnamese
    "id": _rule_other_only,  # Indonesian
    "ms": _rule_other_only,  # Malay
    "tr": _rule_other_only,  # Turkish
    "fa": _rule_other_only,  # Persian
    "lo": _rule_other_only,  # Lao
    "my": _rule_other_only,  # Burmese
    # One + Other (Germanic, etc.)
    "en": _rule_one_other,  # English
    "de": _rule_one_other,  # German
    "nl": _rule_one_other,  # Dutch
    "sv": _rule_one_other,  # Swedish
    "da": _rule_one_other,  # Danish
    "no": _rule_one_other,  # Norwegian
    "nb": _rule_one_other,  # Norwegian Bokmål
    "nn": _rule_one_other,  # Norwegian Nynorsk
    "fi": _rule_one_other,  # Finnish
    "et": _rule_one_other,  # Estonian
    "el": _rule_one_other,  # Greek
    "it": _rule_one_other,  # Italian
    "es": _rule_one_other,  # Spanish
    "ca": _rule_one_other,  # Catalan
    "bg": _rule_one_other,  # Bulgarian
    "hu": _rule_one_other,  # Hungarian
    "he": _rule_one_other,  # Hebrew
    "bn": _rule_one_other,  # Bengali
    "te": _rule_one_other,  # Telugu
    "ta": _rule_one_other,  # Tamil
    "ur": _rule_one_other,  # Urdu
    "sw": _rule_one_other,  # Swahili
    # French rule (0 and 1 are "one")
    "fr": _rule_french,  # French
    "pt": _rule_french,  # Portuguese (Brazilian)
    "hy": _rule_french,  # Armenian
    # Latvian
    "lv": _rule_zero_one_other,
    # Czech/Slovak
    "cs": _rule_czech_slovak,  # Czech
    "sk": _rule_czech_slovak,  # Slovak
    # Polish
    "pl": _rule_polish,
    # Russian/Slavic
    "ru": _rule_russian,  # Russian
    "uk": _rule_russian,  # Ukrainian
    "be": _rule_russian,  # Belarusian
    "sr": _rule_russian,  # Serbian
    "hr": _rule_russian,  # Croatian
    "bs": _rule_russian,  # Bosnian
    # Romanian
    "ro": _rule_romanian,
    "mo": _rule_romanian,  # Moldovan
    # Arabic
    "ar": _rule_arabic,
    # Welsh
    "cy": _rule_welsh,
    # Irish
    "ga": _rule_irish,
    # Maltese
    "mt": _rule_maltese,
    # Slovenian
    "sl": _rule_slovenian,
    # Icelandic
    "is": _rule_icelandic,
    # Lithuanian (similar to Russian but slightly different)
    "lt": _rule_russian,
}


def get_supported_locales() -> list[str]:
    """Get list of all locales with defined plural rules.

    Returns:
        List of locale codes
    """
    return sorted(_PLURAL_RULES.keys())


def get_plural_categories(locale: str) -> list[PluralCategory]:
    """Get all possible plural categories for a locale.

    Args:
        locale: Locale code

    Returns:
        List of plural categories used by this locale
    """
    lang = locale.split("-")[0].split("_")[0].lower()

    # Test with representative numbers to discover which categories are used
    test_numbers = [0, 1, 2, 3, 4, 5, 6, 7, 10, 11, 12, 15, 20, 21, 100, 101]
    categories = set()

    for num in test_numbers:
        category = get_plural_category(locale, num)
        categories.add(category)

    # Return in standard order
    order = ["zero", "one", "two", "few", "many", "other"]
    return [cat for cat in order if cat in categories]
