"""Simple example demonstrating flet_l10n basic usage with global pattern."""

import flet as ft
from flet_l10n import Localizations


def main(page: ft.Page):
    page.title = "flet_l10n Example"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Initialize localization (will auto-detect system locale)
    # For this example, we'll use manual initialization
    try:
        l10n = Localizations.from_config()
    except Exception:
        # Fallback if no config exists
        l10n = Localizations(
            arb_dir="locales",
            default_locale="en",
            fallback_locale="en",
            hot_reload=True,
        )

    # UI components
    title_text = ft.Text(
        l10n.t("appTitle"),
        size=30,
        weight=ft.FontWeight.BOLD,
    )

    welcome_text = ft.Text(
        l10n.t("welcome", name="Flet User"),
        size=20,
    )

    item_count_text = ft.Text(
        l10n.plural("itemCount", count=0),
        size=16,
    )

    def update_ui():
        """Update all translatable UI elements."""
        title_text.value = l10n.t("appTitle")
        welcome_text.value = l10n.t("welcome", name="Flet User")
        item_count_text.value = l10n.plural("itemCount", count=int(count_slider.value))
        page.update()

    def change_language(e):
        """Handle language change."""
        l10n.set_locale(e.control.value)
        update_ui()

    def update_count(e):
        """Handle item count change."""
        item_count_text.value = l10n.plural("itemCount", count=int(e.control.value))
        page.update()

    # Language selector
    language_dropdown = ft.Dropdown(
        label="Language",
        options=[
            ft.dropdown.Option("en", "English"),
            ft.dropdown.Option("es", "Español"),
            ft.dropdown.Option("fr", "Français"),
        ],
        value=l10n.current_locale,
        on_change=change_language,
        width=200,
    )

    # Item count slider
    count_slider = ft.Slider(
        min=0,
        max=10,
        divisions=10,
        value=0,
        label="{value}",
        on_change=update_count,
        width=300,
    )

    # Build UI
    page.add(
        ft.Container(
            content=ft.Column(
                [
                    title_text,
                    ft.Divider(),
                    welcome_text,
                    ft.Container(height=20),
                    language_dropdown,
                    ft.Container(height=20),
                    ft.Text("Adjust item count:", size=14, weight=ft.FontWeight.BOLD),
                    count_slider,
                    item_count_text,
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=40,
        )
    )


if __name__ == "__main__":
    ft.run(main)
