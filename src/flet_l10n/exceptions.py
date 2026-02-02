"""Custom exceptions for flet_l10n package."""


class FletL10nError(Exception):
    """Base exception for all flet_l10n errors."""

    pass


class ARBParseError(FletL10nError):
    """Raised when an ARB file cannot be parsed."""

    def __init__(self, file_path: str, message: str):
        self.file_path = file_path
        super().__init__(f"Error parsing ARB file '{file_path}': {message}")


class LocaleNotFoundError(FletL10nError):
    """Raised when a requested locale is not available."""

    def __init__(self, locale: str, available_locales: list[str]):
        self.locale = locale
        self.available_locales = available_locales
        super().__init__(
            f"Locale '{locale}' not found. Available locales: {', '.join(available_locales)}"
        )


class TranslationKeyError(FletL10nError):
    """Raised when a translation key is not found."""

    def __init__(self, key: str, locale: str):
        self.key = key
        self.locale = locale
        super().__init__(f"Translation key '{key}' not found for locale '{locale}'")


class ConfigurationError(FletL10nError):
    """Raised when l10n.yaml configuration is invalid."""

    def __init__(self, message: str):
        super().__init__(f"Configuration error: {message}")


class ICUFormatError(FletL10nError):
    """Raised when ICU MessageFormat syntax is invalid."""

    def __init__(self, pattern: str, message: str):
        self.pattern = pattern
        super().__init__(f"Invalid ICU format in '{pattern}': {message}")
