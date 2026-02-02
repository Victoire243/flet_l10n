"""Example demonstrating context-based provider pattern with proper UI updates."""

import flet as ft
from flet_l10n import LocalizationsProvider, use_localizations


def main(page: ft.Page):
    page.title = "flet_l10n Provider Example"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 40

    # Initialize LocalizationsProvider
    try:
        provider = LocalizationsProvider(page, config_path="l10n.yaml")
    except Exception:
        # Fallback if no config
        provider = LocalizationsProvider(
            page,
            arb_dir="locales",
            default_locale="en",
            hot_reload=True,
        )

    # Access localization through provider
    l10n = use_localizations(page)

    # Create UI components (imperative pattern)
    title = ft.Text(size=30, weight=ft.FontWeight.BOLD)
    welcome = ft.Text(size=20)
    item_count = ft.Text(size=16)
    current_locale_display = ft.Text(size=14, color=ft.Colors.BLUE_GREY_700)

    # Locale dropdown
    locale_dropdown = ft.Dropdown(
        label="Select Language",
        options=[
            ft.dropdown.Option("en", "English 🇬🇧"),
            ft.dropdown.Option("es", "Español 🇪🇸"),
            ft.dropdown.Option("fr", "Français 🇫🇷"),
        ],
        width=250,
    )

    # Item count selector
    count_slider = ft.Slider(
        min=0,
        max=10,
        divisions=10,
        value=3,
        label="{value}",
        width=300,
    )

    def update_ui():
        """Update all UI components with current translations.

        This function is called automatically when locale changes.
        """
        # Update all text components
        title.value = l10n.t("appTitle")
        welcome.value = l10n.t("welcome", name="User")
        item_count.value = l10n.plural("itemCount", count=int(count_slider.value))
        current_locale_display.value = f"Current locale: {l10n.current_locale}"
        locale_dropdown.value = l10n.current_locale

        # Update page
        page.update()

    def change_locale(e):
        """Change locale when dropdown changes."""
        l10n.set_locale(e.control.value)
        # update_ui() will be called automatically via callback

    def update_count(e):
        """Update item count when slider changes."""
        item_count.value = l10n.plural("itemCount", count=int(e.control.value))
        page.update()

    # Register update callback for automatic UI refresh on locale change
    provider.add_update_callback(update_ui)

    # Set event handlers
    locale_dropdown.on_select = change_locale
    count_slider.on_change = update_count

    # Build UI
    page.add(
        ft.Column(
            [
                title,
                ft.Divider(height=20),
                welcome,
                ft.Container(height=20),
                current_locale_display,
                ft.Container(height=20),
                locale_dropdown,
                ft.Container(height=30),
                ft.Text("Adjust item count:", size=14, weight=ft.FontWeight.BOLD),
                count_slider,
                item_count,
                ft.Container(height=30),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "💡 How it works:", size=14, weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                "• Change language → All components update automatically",
                                size=12,
                            ),
                            ft.Text(
                                "• Uses callback pattern for imperative UI updates",
                                size=12,
                            ),
                            ft.Text(
                                "• No need to manually refresh each component", size=12
                            ),
                        ],
                        spacing=5,
                    ),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=15,
                    border_radius=10,
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=10,
        )
    )

    # Initial UI update
    update_ui()


if __name__ == "__main__":
    ft.run(main)
