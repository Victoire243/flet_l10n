"""Context-based provider pattern for Flet integration."""

from pathlib import Path
from typing import Any, Callable, Optional

try:
    import flet as ft
except ImportError:
    ft = None  # type: ignore

from .localizations import Localizations

# Storage key for Localizations in Flet page session
_LOCALIZATIONS_KEY = "_flet_l10n_instance"
_UPDATE_CALLBACKS_KEY = "_flet_l10n_update_callbacks"


class LocalizationsProvider:
    """Provides context-based localization for Flet applications.

    This class integrates with Flet's page session to provide
    localization context throughout the app.

    Supports both imperative (manual update) and declarative (auto-update) patterns.
    """

    def __init__(
        self,
        page: Any,  # ft.Page
        arb_dir: Optional[str | Path] = None,
        config_path: Optional[str | Path] = None,
        default_locale: Optional[str] = None,
        fallback_locale: str = "en",
        hot_reload: bool = False,
    ):
        """Initialize localization provider for a Flet page.

        Args:
            page: Flet Page object
            arb_dir: Directory containing ARB files (used if config_path is None)
            config_path: Path to l10n.yaml configuration file
            default_locale: Default locale (auto-detected if None)
            fallback_locale: Fallback locale
            hot_reload: Enable hot-reload during development

        Note:
            Either arb_dir or config_path must be provided.
            If config_path is provided, other args are ignored.

        Example:
            ```python
            import flet as ft
            from flet_l10n import LocalizationsProvider, use_localizations

            def main(page: ft.Page):
                # Initialize provider
                provider = LocalizationsProvider(page, arb_dir="locales")

                # Register update callback for imperative pattern
                def update_ui():
                    title.value = provider.localizations.t("appTitle")
                    page.update()

                provider.add_update_callback(update_ui)

                title = ft.Text()
                update_ui()  # Initial update

                page.add(title)

            ft.app(target=main)
            ```
        """
        if ft is None:
            raise ImportError("Flet is not installed. Install with: pip install flet")

        self.page = page
        self._update_callbacks: list[Callable[[], None]] = []

        # Create or load Localizations instance
        if config_path:
            self.localizations = Localizations.from_config(config_path)
        elif arb_dir:
            self.localizations = Localizations(
                arb_dir=arb_dir,
                default_locale=default_locale,
                fallback_locale=fallback_locale,
                hot_reload=hot_reload,
            )
        else:
            raise ValueError("Either arb_dir or config_path must be provided")

        # Store in page session
        if not hasattr(page, "session") or page.session is None:
            # For older Flet versions or testing
            page._l10n = self.localizations  # type: ignore
            page._l10n_callbacks = self._update_callbacks  # type: ignore
        else:
            # Try different session APIs (varies by Flet version)
            session = page.session.store
            if hasattr(session, "set"):
                session.set(_LOCALIZATIONS_KEY, self.localizations)
                session.set(_UPDATE_CALLBACKS_KEY, self._update_callbacks)
            else:
                # Fallback to page attributes (most compatible)
                page._l10n = self.localizations  # type: ignore
                page._l10n_callbacks = self._update_callbacks  # type: ignore

        # Register callback to update page on locale change
        self.localizations.on_locale_change(self._on_locale_change)

    def add_update_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback to be called when locale changes.

        Use this for imperative pattern where you manually update components.

        Args:
            callback: Function to call when locale changes (no arguments)

        Example:
            ```python
            def update_ui():
                title.value = l10n.t("appTitle")
                welcome.value = l10n.t("welcome", name="User")
                page.update()

            provider.add_update_callback(update_ui)
            ```
        """
        if callback not in self._update_callbacks:
            self._update_callbacks.append(callback)

    def remove_update_callback(self, callback: Callable[[], None]) -> None:
        """Unregister an update callback.

        Args:
            callback: The callback to remove
        """
        if callback in self._update_callbacks:
            self._update_callbacks.remove(callback)

    def _on_locale_change(self, new_locale: str) -> None:
        """Handle locale change by calling all registered callbacks.

        Args:
            new_locale: The new locale code
        """
        # Call all registered update callbacks
        for callback in self._update_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error in locale change callback: {e}")

    @staticmethod
    def get(page: Any) -> Optional[Localizations]:
        """Get Localizations instance from page context.

        Args:
            page: Flet Page object

        Returns:
            Localizations instance or None if not found
        """
        # Prefer direct page attribute (most compatible)
        if hasattr(page, "_l10n"):
            return page._l10n  # type: ignore

        # Try session.get() for newer Flet versions
        if hasattr(page, "session") and page.session is not None:
            session = page.session.store
            if hasattr(session, "get"):
                result = session.get(_LOCALIZATIONS_KEY)
                if result is not None:
                    return result

        return None

    @staticmethod
    def get_provider_callbacks(page: Any) -> list[Callable[[], None]]:
        """Get registered update callbacks from page context.

        Args:
            page: Flet Page object

        Returns:
            List of callbacks or empty list if not found
        """
        # Prefer direct page attribute (most compatible)
        if hasattr(page, "_l10n_callbacks"):
            return page._l10n_callbacks  # type: ignore

        # Try session.get() for newer Flet versions
        if hasattr(page, "session") and page.session is not None:
            session = page.session.store
            if hasattr(session, "get"):
                result = session.get(_UPDATE_CALLBACKS_KEY)
                if result is not None:
                    return result

        return []


def use_localizations(page: Any) -> Localizations:
    """Get Localizations instance from Flet page context.

    This is the recommended way to access localization in Flet apps
    when using the context-based pattern.

    Args:
        page: Flet Page object

    Returns:
        Localizations instance

    Raises:
        RuntimeError: If LocalizationsProvider has not been initialized

    Example (Imperative Pattern):
        ```python
        import flet as ft
        from flet_l10n import LocalizationsProvider, use_localizations

        def main(page: ft.Page):
            # Initialize provider
            provider = LocalizationsProvider(page, arb_dir="locales")

            # Create UI components
            title = ft.Text()
            welcome = ft.Text()

            # Define update function
            def update_ui():
                l10n = use_localizations(page)
                title.value = l10n.t("appTitle")
                welcome.value = l10n.t("welcome", name="User")
                page.update()

            # Register callback
            provider.add_update_callback(update_ui)

            # Initial update
            update_ui()

            # Language switcher
            def change_lang(e):
                l10n = use_localizations(page)
                l10n.set_locale(e.control.value)
                # update_ui() will be called automatically

            page.add(
                title,
                welcome,
                ft.Dropdown(
                    options=[
                        ft.dropdown.Option("en", "English"),
                        ft.dropdown.Option("es", "Español"),
                    ],
                    on_change=change_lang,
                ),
            )

        ft.app(target=main)
        ```

    Example (Declarative Pattern with Flet States):
        ```python
        import flet as ft
        from flet_l10n import LocalizationsProvider, use_localizations

        def main(page: ft.Page):
            provider = LocalizationsProvider(page, arb_dir="locales")

            # Use reactive state (Flet 0.80+)
            locale_state = ft.Text(value="")

            def update_ui():
                l10n = use_localizations(page)
                locale_state.value = l10n.current_locale
                page.update()

            provider.add_update_callback(update_ui)
            update_ui()

            page.add(
                # Components will re-render when locale changes
                ft.Text(lambda: use_localizations(page).t("appTitle")),
            )

        ft.app(target=main)
        ```
    """
    localizations = LocalizationsProvider.get(page)

    if localizations is None:
        raise RuntimeError(
            "LocalizationsProvider has not been initialized for this page. "
            "Initialize it with: LocalizationsProvider(page, arb_dir='locales')"
        )

    return localizations


# Convenience function for quick access
def t(page: Any, key: str, **kwargs: Any) -> str:
    """Translate a key using page context (shorthand).

    Args:
        page: Flet Page object
        key: Translation key
        **kwargs: Placeholder values

    Returns:
        Translated string

    Example:
        ```python
        page.add(ft.Text(t(page, "greeting", name="World")))
        ```
    """
    l10n = use_localizations(page)
    return l10n.t(key, **kwargs)
