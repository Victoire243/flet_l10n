"""Example of using typed keys for IDE autocompletion and type safety."""

import sys
from pathlib import Path

# Add parent directory to path to import l10n_keys
sys.path.insert(0, str(Path(__file__).parent.parent))

import flet as ft
from flet_l10n import Localizations
from l10n_keys import L10nKeys  # Provides IDE autocompletion


def main(page: ft.Page):
    """Demonstration of typed keys usage."""
    page.title = "Typed Keys Example"
    page.padding = 20

    # Initialize localizations
    l10n = Localizations.from_config()

    # UI elements
    title = ft.Text(size=24, weight=ft.FontWeight.BOLD)
    welcome_msg = ft.Text(size=18)
    items_text = ft.Text(size=16)

    def update_ui():
        """Update all UI elements with current locale."""
        # Using typed keys - IDE will autocomplete L10nKeys.appTitle, L10nKeys.welcome, etc.
        title.value = l10n.t(L10nKeys.appTitle)
        welcome_msg.value = l10n.t(L10nKeys.welcome, name="Alice")

        # Can also use Keys instance
        items_text.value = l10n.t(L10nKeys.itemCount, count=5)

        page.update()

    def on_locale_change(locale):
        """Callback when locale changes."""
        print(f"Locale changed to: {locale}")
        update_ui()

    l10n.on_locale_change(on_locale_change)
    update_ui()

    # Locale switcher buttons
    def switch_to_en(e):
        l10n.set_locale("en")

    def switch_to_es(e):
        l10n.set_locale("es")

    def switch_to_fr(e):
        l10n.set_locale("fr")

    page.add(
        title,
        ft.Divider(height=20),
        welcome_msg,
        items_text,
        ft.Divider(height=20),
        ft.Text("Switch Language:", size=16, weight=ft.FontWeight.BOLD),
        ft.Row(
            [
                ft.ElevatedButton("English", on_click=switch_to_en),
                ft.ElevatedButton("Español", on_click=switch_to_es),
                ft.ElevatedButton("Français", on_click=switch_to_fr),
            ],
            spacing=10,
        ),
        ft.Divider(height=20),
        ft.Text(
            "Benefits of typed keys:",
            size=14,
            weight=ft.FontWeight.BOLD,
        ),
        ft.Column(
            [
                ft.Text("• IDE autocompletion for all keys", size=12),
                ft.Text("• Catch typos at edit time", size=12),
                ft.Text("• Jump to definition support", size=12),
                ft.Text("• Refactoring support", size=12),
                ft.Text(
                    "• Type hints show available placeholders in docstrings", size=12
                ),
            ],
            spacing=5,
        ),
    )


if __name__ == "__main__":
    ft.run(main)
