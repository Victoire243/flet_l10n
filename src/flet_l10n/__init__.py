"""flet_l10n - Localization support for Flet applications.

This package provides Flutter-inspired localization for Flet apps using ARB files
and ICU MessageFormat with full CLDR plural rules support.
"""

__version__ = "0.1.3"

from .localizations import Localizations
from .providers import LocalizationsProvider, use_localizations, t
from .config import L10nConfig
from .generator import L10nKeysGenerator, generate_keys_class
from .exceptions import (
    FletL10nError,
    ARBParseError,
    LocaleNotFoundError,
    TranslationKeyError,
    ConfigurationError,
    ICUFormatError,
)

__all__ = [
    # Main classes
    "Localizations",
    "LocalizationsProvider",
    "L10nConfig",
    "L10nKeysGenerator",
    # Helper functions
    "use_localizations",
    "t",
    "generate_keys_class",
    # Exceptions
    "FletL10nError",
    "ARBParseError",
    "LocaleNotFoundError",
    "TranslationKeyError",
    "ConfigurationError",
    "ICUFormatError",
    # Version
    "__version__",
]
