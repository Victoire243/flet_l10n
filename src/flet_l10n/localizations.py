"""Main localization class for Flet applications."""

import locale as sys_locale
import logging
from pathlib import Path
from typing import Any, Optional, Callable

from .config import L10nConfig
from .exceptions import TranslationKeyError, LocaleNotFoundError
from .formatters import MessageFormatter
from .hot_reload import HotReloadWatcher
from .locale_manager import LocaleManager
from .translation_loader import TranslationLoader

logger = logging.getLogger(__name__)


class Localizations:
    """Main localization class providing translation services for Flet apps."""

    def __init__(
        self,
        arb_dir: str | Path,
        default_locale: Optional[str] = None,
        fallback_locale: str = "en",
        supported_locales: Optional[list[str]] = None,
        hot_reload: bool = False,
        auto_detect_locale: bool = True,
    ):
        """Initialize localization system.

        Args:
            arb_dir: Directory containing ARB files
            default_locale: Default locale (auto-detected if None and auto_detect_locale=True)
            fallback_locale: Fallback locale when translation is missing
            supported_locales: List of supported locales (auto-discovered if None)
            hot_reload: Enable hot-reload of ARB files during development
            auto_detect_locale: Automatically detect system locale on initialization
        """
        self.arb_dir = Path(arb_dir)

        # Initialize translation loader
        self.loader = TranslationLoader(self.arb_dir)

        # Discover available locales if not provided
        if supported_locales is None:
            supported_locales = self.loader.discover_locales()

        if not supported_locales:
            logger.warning(f"No ARB files found in {self.arb_dir}")
            supported_locales = [fallback_locale]

        # Initialize locale manager
        self.locale_manager = LocaleManager(supported_locales, fallback_locale)

        # Auto-detect system locale if requested
        if default_locale is None and auto_detect_locale:
            default_locale = self._detect_system_locale()
        elif default_locale is None:
            default_locale = fallback_locale

        # Resolve default locale
        self._current_locale = self.locale_manager.resolve_locale(default_locale)

        # Initialize formatter
        self.formatter = MessageFormatter(self._current_locale)

        # Hot-reload watcher
        self._hot_reload_watcher: Optional[HotReloadWatcher] = None
        if hot_reload:
            self.enable_hot_reload()

        # Callbacks for locale changes
        self._on_locale_change_callbacks: list[Callable[[str], None]] = []

        logger.info(
            f"Localizations initialized: locale={self._current_locale}, "
            f"fallback={fallback_locale}, supported={supported_locales}"
        )

    @classmethod
    def from_config(cls, config_path: Optional[str | Path] = None) -> "Localizations":
        """Create Localizations instance from l10n.yaml configuration.

        Args:
            config_path: Path to l10n.yaml file (searches if None)

        Returns:
            Localizations instance
        """
        config = L10nConfig.from_yaml(config_path)
        config.validate()

        return cls(
            arb_dir=config.arb_dir,
            default_locale=config.default_locale,
            fallback_locale=config.fallback_locale,
            supported_locales=(
                config.supported_locales if config.supported_locales else None
            ),
            hot_reload=config.hot_reload,
        )

    @staticmethod
    def _detect_system_locale() -> str:
        """Detect the system's default locale.

        Returns:
            Detected locale code (e.g., 'en', 'en-US')
        """
        try:
            # Get system locale
            system_locale = sys_locale.getdefaultlocale()[0]
            if system_locale:
                # Convert to standard format (en_US -> en-US)
                return system_locale.replace("_", "-")
        except Exception as e:
            logger.warning(f"Could not detect system locale: {e}")

        return "en"  # Default fallback

    @property
    def current_locale(self) -> str:
        """Get the current active locale."""
        return self._current_locale

    @property
    def supported_locales(self) -> list[str]:
        """Get list of supported locales."""
        return self.locale_manager.supported_locales

    @property
    def fallback_locale(self) -> str:
        """Get the fallback locale."""
        return self.locale_manager.fallback_locale

    def set_locale(self, locale: str) -> None:
        """Change the current locale.

        Args:
            locale: New locale code

        Raises:
            LocaleNotFoundError: If locale is not supported
        """
        # Resolve locale
        resolved = self.locale_manager.resolve_locale(locale)

        # Check if locale is available
        if not self.loader._find_arb_file(resolved):
            available = self.loader.discover_locales()
            raise LocaleNotFoundError(locale, available)

        old_locale = self._current_locale
        self._current_locale = resolved

        # Update formatter locale
        self.formatter = MessageFormatter(self._current_locale)

        logger.info(f"Locale changed: {old_locale} -> {self._current_locale}")

        # Notify callbacks
        self._notify_locale_change(self._current_locale)

    def translate(self, key: str, **kwargs: Any) -> str:
        """Translate a key with optional placeholder values.

        Args:
            key: Translation key
            **kwargs: Values for placeholders in the translation

        Returns:
            Translated and formatted string

        Raises:
            TranslationKeyError: If key is not found in any locale in fallback chain
        """
        # Try current locale and fallback chain
        fallback_chain = self.locale_manager.get_fallback_chain(self._current_locale)

        for locale in fallback_chain:
            entry = self.loader.get_translation(locale, key)
            if entry:
                # Format the translation
                try:
                    return self.formatter.format(entry.value, **kwargs)
                except Exception as e:
                    logger.error(f"Error formatting translation '{key}': {e}")
                    # Return unformatted value as fallback
                    return entry.value

        # Key not found in any locale
        raise TranslationKeyError(key, self._current_locale)

    def t(self, key: str, **kwargs: Any) -> str:
        """Shorthand for translate().

        Args:
            key: Translation key
            **kwargs: Values for placeholders

        Returns:
            Translated and formatted string
        """
        return self.translate(key, **kwargs)

    def has_key(self, key: str, locale: Optional[str] = None) -> bool:
        """Check if a translation key exists.

        Args:
            key: Translation key
            locale: Locale to check (current locale if None)

        Returns:
            True if key exists
        """
        if locale is None:
            locale = self._current_locale

        entry = self.loader.get_translation(locale, key)
        return entry is not None

    def plural(self, key: str, count: int | float, **kwargs: Any) -> str:
        """Translate a plural key with count.

        This is a convenience method that adds the count to kwargs.

        Args:
            key: Translation key with plural syntax
            count: Number for plural selection
            **kwargs: Additional placeholder values

        Returns:
            Translated and formatted string
        """
        kwargs["count"] = count
        return self.translate(key, **kwargs)

    def enable_hot_reload(
        self, callback: Optional[Callable[[str], None]] = None
    ) -> None:
        """Enable hot-reload of ARB files.

        Args:
            callback: Optional callback function called when files change
        """
        if self._hot_reload_watcher and self._hot_reload_watcher.is_watching:
            logger.warning("Hot-reload is already enabled")
            return

        def on_change(file_path: str):
            logger.info(f"Reloading translations due to change in: {file_path}")
            self.loader.reload_all()
            if callback:
                callback(file_path)

        self._hot_reload_watcher = HotReloadWatcher(self.arb_dir, on_change)
        self._hot_reload_watcher.start()
        logger.info("Hot-reload enabled")

    def disable_hot_reload(self) -> None:
        """Disable hot-reload of ARB files."""
        if self._hot_reload_watcher:
            self._hot_reload_watcher.stop()
            self._hot_reload_watcher = None
            logger.info("Hot-reload disabled")

    def reload_translations(self) -> None:
        """Manually reload all translations from ARB files."""
        self.loader.reload_all()
        logger.info("Translations reloaded")

    def on_locale_change(self, callback: Callable[[str], None]) -> None:
        """Register a callback to be called when locale changes.

        Args:
            callback: Function that takes the new locale as argument
        """
        if callback not in self._on_locale_change_callbacks:
            self._on_locale_change_callbacks.append(callback)

    def _notify_locale_change(self, new_locale: str) -> None:
        """Notify all registered callbacks about locale change.

        Args:
            new_locale: The new locale code
        """
        for callback in self._on_locale_change_callbacks:
            try:
                callback(new_locale)
            except Exception as e:
                logger.error(f"Error in locale change callback: {e}", exc_info=True)

    def get_all_keys(self, locale: Optional[str] = None) -> list[str]:
        """Get all translation keys for a locale.

        Args:
            locale: Locale to get keys for (current locale if None)

        Returns:
            List of translation keys
        """
        if locale is None:
            locale = self._current_locale

        try:
            entries = self.loader.load_locale(locale)
            return list(entries.keys())
        except LocaleNotFoundError:
            return []

    def __del__(self) -> None:
        """Cleanup on deletion."""
        if self._hot_reload_watcher:
            self._hot_reload_watcher.stop()
