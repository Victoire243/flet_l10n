"""Example showing alternative pattern with full UI rebuild on locale change."""

import flet as ft
from flet_l10n import LocalizationsProvider, use_localizations


def main(page: ft.Page):
    """Alternative pattern: Rebuild entire UI on locale change.

    This pattern is simpler but less efficient for complex UIs.
    Good for small apps or when components are tightly coupled.
    """
    page.title = "flet_l10n Rebuild Pattern"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 40

    # Initialize provider
    try:
        provider = LocalizationsProvider(page, config_path="l10n.yaml")
    except Exception:
        provider = LocalizationsProvider(page, arb_dir="locales", default_locale="en")

    def build_ui():
        """Build the entire UI with current locale."""
        l10n = use_localizations(page)

        def change_locale(e):
            """Change locale and rebuild entire UI."""
            l10n.set_locale(e.control.value)

        return ft.Column(
            [
                ft.Text(
                    l10n.t("appTitle"),
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=ft.Colors.BLUE_900,
                ),
                ft.Divider(height=20),
                ft.Text(
                    l10n.t("welcome", name="Rebuild User"),
                    size=20,
                    color=ft.Colors.GREY_800,
                ),
                ft.Container(height=20),
                ft.Row(
                    [
                        ft.Icon(ft.Icons.LANGUAGE, color=ft.Colors.BLUE_700),
                        ft.Dropdown(
                            label="Language",
                            options=[
                                ft.dropdown.Option("en", "English 🇬🇧"),
                                ft.dropdown.Option("es", "Español 🇪🇸"),
                                ft.dropdown.Option("fr", "Français 🇫🇷"),
                            ],
                            value=l10n.current_locale,
                            on_select=change_locale,
                            width=200,
                        ),
                    ],
                    spacing=10,
                ),
                ft.Container(height=20),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(l10n.plural("itemCount", count=0), size=14),
                            ft.Text(l10n.plural("itemCount", count=1), size=14),
                            ft.Text(l10n.plural("itemCount", count=5), size=14),
                        ],
                        spacing=5,
                    ),
                    bgcolor=ft.Colors.GREY_100,
                    padding=15,
                    border_radius=10,
                ),
                ft.Container(height=30),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                "ℹ️ Rebuild Pattern",
                                size=14,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_900,
                            ),
                            ft.Text(
                                "• Entire UI is rebuilt on locale change",
                                size=12,
                                color=ft.Colors.GREY_700,
                            ),
                            ft.Text(
                                "• Simpler code, no manual updates needed",
                                size=12,
                                color=ft.Colors.GREY_700,
                            ),
                            ft.Text(
                                "• Best for small apps or simple UIs",
                                size=12,
                                color=ft.Colors.GREY_700,
                            ),
                        ],
                        spacing=5,
                    ),
                    bgcolor=ft.Colors.BLUE_50,
                    padding=15,
                    border_radius=10,
                    border=ft.border.all(1, ft.Colors.BLUE_200),
                ),
            ],
            horizontal_alignment=ft.CrossAxisAlignment.START,
            spacing=10,
        )

    def rebuild_ui():
        """Rebuild entire UI."""
        page.clean()
        page.add(build_ui())
        page.update()

    # Register callback to rebuild UI on locale change
    provider.add_update_callback(rebuild_ui)

    # Initial UI build
    page.add(build_ui())


if __name__ == "__main__":
    ft.run(main)
