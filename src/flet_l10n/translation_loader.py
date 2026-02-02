"""Translation loader with lazy loading and caching."""

from pathlib import Path
from typing import Any

from .arb_parser import ARBParser, ARBEntry, extract_locale_from_filename
from .exceptions import LocaleNotFoundError, ARBParseError


class TranslationLoader:
    """Loads and caches translations from ARB files with lazy loading."""

    def __init__(self, arb_dir: Path | str):
        """Initialize translation loader.

        Args:
            arb_dir: Directory containing ARB files
        """
        self.arb_dir = Path(arb_dir)
        self._cache: dict[str, dict[str, ARBEntry]] = {}
        self._available_locales: list[str] | None = None

    def discover_locales(self) -> list[str]:
        """Discover available locales from ARB files in the directory.

        Returns:
            List of locale codes found in ARB files
        """
        if self._available_locales is not None:
            return self._available_locales

        if not self.arb_dir.exists():
            return []

        locales = []
        parser = ARBParser()

        for arb_file in self.arb_dir.glob("*.arb"):
            try:
                # Try to parse file to get @@locale
                entries = parser.parse_file(arb_file)
                if parser.locale:
                    locales.append(parser.locale)
                else:
                    # Fall back to extracting from filename
                    locale = extract_locale_from_filename(arb_file.name)
                    if locale:
                        locales.append(locale)
            except ARBParseError:
                # Skip invalid files
                continue

        self._available_locales = sorted(set(locales))
        return self._available_locales

    def load_locale(self, locale: str) -> dict[str, ARBEntry]:
        """Load translations for a specific locale (lazy loading with cache).

        Args:
            locale: Locale code to load

        Returns:
            Dictionary mapping translation keys to ARBEntry objects

        Raises:
            LocaleNotFoundError: If locale is not available
        """
        # Check cache first
        if locale in self._cache:
            return self._cache[locale]

        # Find ARB file for this locale
        arb_file = self._find_arb_file(locale)
        if not arb_file:
            available = self.discover_locales()
            raise LocaleNotFoundError(locale, available)

        # Parse ARB file
        parser = ARBParser()
        entries = parser.parse_file(arb_file)

        # Cache the entries
        self._cache[locale] = entries

        return entries

    def _find_arb_file(self, locale: str) -> Path | None:
        """Find the ARB file for a given locale.

        Args:
            locale: Locale code

        Returns:
            Path to ARB file or None if not found
        """
        if not self.arb_dir.exists():
            return None

        # Try common naming patterns
        patterns = [
            f"*_{locale}.arb",  # app_en.arb, intl_es.arb
            f"*-{locale}.arb",  # app-en.arb
            f"{locale}.arb",  # en.arb
        ]

        for pattern in patterns:
            matches = list(self.arb_dir.glob(pattern))
            if matches:
                return matches[0]

        # Try case-insensitive match
        locale_lower = locale.lower()
        for arb_file in self.arb_dir.glob("*.arb"):
            file_locale = extract_locale_from_filename(arb_file.name)
            if file_locale and file_locale.lower() == locale_lower:
                return arb_file

        return None

    def reload_locale(self, locale: str) -> dict[str, ARBEntry]:
        """Reload translations for a locale, clearing cache.

        Args:
            locale: Locale code to reload

        Returns:
            Dictionary of reloaded translations

        Raises:
            LocaleNotFoundError: If locale is not available
        """
        # Clear cache for this locale
        if locale in self._cache:
            del self._cache[locale]

        # Reload
        return self.load_locale(locale)

    def reload_all(self) -> None:
        """Reload all cached translations."""
        locales_to_reload = list(self._cache.keys())
        self._cache.clear()
        self._available_locales = None

        # Re-discover locales
        self.discover_locales()

        # Reload previously loaded locales
        for locale in locales_to_reload:
            try:
                self.load_locale(locale)
            except LocaleNotFoundError:
                # Locale no longer available, skip
                pass

    def get_translation(self, locale: str, key: str) -> ARBEntry | None:
        """Get a specific translation entry.

        Args:
            locale: Locale code
            key: Translation key

        Returns:
            ARBEntry or None if not found
        """
        try:
            entries = self.load_locale(locale)
            return entries.get(key)
        except LocaleNotFoundError:
            return None

    def clear_cache(self) -> None:
        """Clear all cached translations."""
        self._cache.clear()
        self._available_locales = None

    @property
    def cached_locales(self) -> list[str]:
        """Get list of currently cached locales."""
        return list(self._cache.keys())

    def is_loaded(self, locale: str) -> bool:
        """Check if a locale is currently loaded in cache.

        Args:
            locale: Locale code

        Returns:
            True if locale is cached
        """
        return locale in self._cache

    def preload_locales(self, locales: list[str]) -> None:
        """Preload multiple locales into cache.

        Args:
            locales: List of locale codes to preload
        """
        for locale in locales:
            try:
                self.load_locale(locale)
            except LocaleNotFoundError:
                # Skip unavailable locales
                pass
