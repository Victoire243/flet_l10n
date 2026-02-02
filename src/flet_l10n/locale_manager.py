"""Locale management and resolution with fallback support."""

from typing import Sequence


class LocaleManager:
    """Manages locale selection, resolution, and fallback chains."""

    def __init__(self, supported_locales: Sequence[str], fallback_locale: str = "en"):
        """Initialize locale manager.

        Args:
            supported_locales: List of supported locale codes
            fallback_locale: Fallback locale when requested locale is not available
        """
        self.supported_locales = list(supported_locales)
        self.fallback_locale = fallback_locale

        # Validate fallback is in supported locales
        if fallback_locale not in self.supported_locales:
            self.supported_locales.append(fallback_locale)

    def resolve_locale(self, locale: str) -> str:
        """Resolve a locale to a supported locale with fallback.

        Args:
            locale: Requested locale code (e.g., 'en-US', 'es', 'zh_CN')

        Returns:
            Resolved locale code from supported locales
        """
        # Normalize locale code
        locale = self._normalize_locale(locale)

        # Try exact match first
        if locale in self.supported_locales:
            return locale

        # Try language-only match (e.g., 'en-US' -> 'en')
        language = locale.split("-")[0].split("_")[0]
        if language in self.supported_locales:
            return language

        # Try to find any locale with the same language
        for supported in self.supported_locales:
            supported_lang = supported.split("-")[0].split("_")[0]
            if supported_lang == language:
                return supported

        # Fall back to default
        return self.fallback_locale

    def get_fallback_chain(self, locale: str) -> list[str]:
        """Get the fallback chain for a locale.

        The chain includes:
        1. The exact locale (if supported)
        2. The language-only locale (if different and supported)
        3. The fallback locale

        Args:
            locale: Locale code

        Returns:
            List of locales in fallback order
        """
        chain = []
        locale = self._normalize_locale(locale)

        # Add exact locale if supported
        if locale in self.supported_locales:
            chain.append(locale)

        # Add language-only variant
        language = locale.split("-")[0].split("_")[0]
        if language != locale and language in self.supported_locales:
            if language not in chain:
                chain.append(language)

        # Add any other locale with same language
        for supported in self.supported_locales:
            supported_lang = supported.split("-")[0].split("_")[0]
            if supported_lang == language and supported not in chain:
                chain.append(supported)
                break

        # Add fallback locale
        if self.fallback_locale not in chain:
            chain.append(self.fallback_locale)

        return chain

    def is_supported(self, locale: str) -> bool:
        """Check if a locale is directly supported.

        Args:
            locale: Locale code

        Returns:
            True if locale is in supported locales list
        """
        locale = self._normalize_locale(locale)
        return locale in self.supported_locales

    def add_locale(self, locale: str) -> None:
        """Add a locale to supported locales.

        Args:
            locale: Locale code to add
        """
        locale = self._normalize_locale(locale)
        if locale not in self.supported_locales:
            self.supported_locales.append(locale)

    def remove_locale(self, locale: str) -> None:
        """Remove a locale from supported locales.

        Args:
            locale: Locale code to remove

        Raises:
            ValueError: If trying to remove the fallback locale
        """
        locale = self._normalize_locale(locale)

        if locale == self.fallback_locale:
            raise ValueError(f"Cannot remove fallback locale '{locale}'")

        if locale in self.supported_locales:
            self.supported_locales.remove(locale)

    @staticmethod
    def _normalize_locale(locale: str) -> str:
        """Normalize locale code to standard format.

        Converts various formats to a standard format:
        - 'en_US' -> 'en-US'
        - 'en' -> 'en'
        - 'EN' -> 'en'
        - 'en-us' -> 'en-US'

        Args:
            locale: Locale code in any format

        Returns:
            Normalized locale code
        """
        if not locale:
            return "en"

        # Replace underscore with hyphen
        locale = locale.replace("_", "-")

        # Split by hyphen
        parts = locale.split("-")

        # Lowercase language code
        if parts:
            parts[0] = parts[0].lower()

        # Uppercase country/script code
        if len(parts) > 1:
            parts[1] = parts[1].upper()

        return "-".join(parts)

    @staticmethod
    def parse_locale(locale: str) -> tuple[str, str | None]:
        """Parse locale code into language and region.

        Args:
            locale: Locale code (e.g., 'en-US', 'es', 'zh-CN')

        Returns:
            Tuple of (language, region) where region may be None
        """
        locale = LocaleManager._normalize_locale(locale)
        parts = locale.split("-")

        language = parts[0] if parts else "en"
        region = parts[1] if len(parts) > 1 else None

        return language, region

    def get_closest_match(
        self, requested_locale: str, available_locales: list[str]
    ) -> str:
        """Get the closest matching locale from available locales.

        Args:
            requested_locale: Requested locale
            available_locales: List of available locales

        Returns:
            Best matching locale from available_locales
        """
        if not available_locales:
            return self.fallback_locale

        requested_locale = self._normalize_locale(requested_locale)

        # Try exact match
        if requested_locale in available_locales:
            return requested_locale

        # Try language match
        req_lang, req_region = self.parse_locale(requested_locale)

        # First, try to find exact language-region match
        for locale in available_locales:
            lang, region = self.parse_locale(locale)
            if lang == req_lang and region == req_region:
                return locale

        # Then, try to find any locale with same language
        for locale in available_locales:
            lang, _ = self.parse_locale(locale)
            if lang == req_lang:
                return locale

        # Return fallback if it's in available locales
        if self.fallback_locale in available_locales:
            return self.fallback_locale

        # Return first available locale
        return available_locales[0]
