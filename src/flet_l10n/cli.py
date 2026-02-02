"""CLI commands for flet_l10n package."""

import json
import sys
from pathlib import Path
from typing import Optional

import click
import yaml
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint

from .arb_parser import ARBParser
from .config import L10nConfig
from .exceptions import ARBParseError, ConfigurationError
from .generator import L10nKeysGenerator
from .plural_rules import get_plural_categories
from .translation_loader import TranslationLoader

console = Console()


@click.group()
@click.version_option()
def cli():
    """flet_l10n - Localization support for Flet applications."""
    pass


@cli.command()
@click.option(
    "--arb-dir",
    default="locales",
    help="Directory for ARB files (default: locales)",
)
@click.option(
    "--default-locale",
    default="en",
    help="Default locale (default: en)",
)
@click.option(
    "--template-arb-file",
    default=None,
    help="Template ARB filename (default: app_{locale}.arb)",
)
@click.option(
    "--hot-reload/--no-hot-reload",
    default=True,
    help="Enable hot-reload in development (default: enabled)",
)
def init(
    arb_dir: str,
    default_locale: str,
    template_arb_file: Optional[str],
    hot_reload: bool,
):
    """Initialize l10n configuration and create template files."""
    arb_path = Path(arb_dir)

    # Create ARB directory
    if not arb_path.exists():
        arb_path.mkdir(parents=True, exist_ok=True)
        console.print(f"✓ Created directory: {arb_dir}", style="green")
    else:
        console.print(f"Directory already exists: {arb_dir}", style="yellow")

    # Create l10n.yaml
    config_path = Path("l10n.yaml")
    if config_path.exists():
        console.print("l10n.yaml already exists", style="yellow")
        if not click.confirm("Overwrite?"):
            return

    config_data = {
        "arb-dir": arb_dir,
        "default-locale": default_locale,
        "fallback-locale": default_locale,
        "template-arb-file": template_arb_file or f"app_{default_locale}.arb",
        "hot-reload": hot_reload,
    }

    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, default_flow_style=False, sort_keys=False)

    console.print(f"✓ Created configuration: l10n.yaml", style="green")

    # Create template ARB file
    template_filename = template_arb_file or f"app_{default_locale}.arb"
    template_path = arb_path / template_filename

    if not template_path.exists():
        template_content = {
            "@@locale": default_locale,
            "@@last_modified": "2026-02-02T00:00:00.000",
            "appTitle": "My Application",
            "@appTitle": {"description": "The title of the application"},
            "welcome": "Welcome, {name}!",
            "@welcome": {
                "description": "Welcome message with user name",
                "placeholders": {"name": {"type": "String", "example": "John"}},
            },
            "itemCount": "{count, plural, =0{No items} one{One item} other{{count} items}}",
            "@itemCount": {
                "description": "Display item count with pluralization",
                "placeholders": {"count": {"type": "int"}},
            },
        }

        with open(template_path, "w", encoding="utf-8") as f:
            json.dump(template_content, f, indent=2, ensure_ascii=False)

        console.print(f"✓ Created template: {template_path}", style="green")
    else:
        console.print(f"Template already exists: {template_path}", style="yellow")

    # Print success message
    rprint("\n[bold green]✓ Initialization complete![/bold green]")
    rprint("\n[bold]Next steps:[/bold]")
    rprint(f"  1. Edit {template_path} to add your translations")
    rprint(f"  2. Run 'flet-l10n add-locale <code>' to add more languages")
    rprint("  3. Use in your Flet app:")
    rprint("     [dim]from flet_l10n import Localizations[/dim]")
    rprint("     [dim]l10n = Localizations.from_config()[/dim]")


@cli.command()
@click.argument("locale_code")
@click.option(
    "--from-template",
    default=None,
    help="Copy from template ARB file",
)
@click.option(
    "--config",
    default=None,
    help="Path to l10n.yaml (searches automatically if not specified)",
)
def add_locale(locale_code: str, from_template: Optional[str], config: Optional[str]):
    """Add a new locale by creating an ARB file."""
    try:
        # Load configuration
        if config:
            l10n_config = L10nConfig.from_yaml(config)
        else:
            try:
                l10n_config = L10nConfig.from_yaml()
            except ConfigurationError:
                console.print(
                    "Error: l10n.yaml not found. Run 'flet-l10n init' first.",
                    style="red",
                )
                sys.exit(1)

        # Determine template file
        if from_template:
            template_path = Path(from_template)
        elif l10n_config.template_arb_file:
            template_path = l10n_config.arb_dir / l10n_config.template_arb_file
        else:
            # Find any ARB file as template
            arb_files = list(l10n_config.arb_dir.glob("*.arb"))
            if not arb_files:
                console.print(
                    "Error: No template ARB file found. Create one first.", style="red"
                )
                sys.exit(1)
            template_path = arb_files[0]

        if not template_path.exists():
            console.print(
                f"Error: Template file not found: {template_path}", style="red"
            )
            sys.exit(1)

        # Parse template
        parser = ARBParser()
        template_entries = parser.parse_file(template_path)

        # Create new ARB file
        new_filename = template_path.name.replace(
            parser.locale or l10n_config.default_locale, locale_code
        )
        new_path = l10n_config.arb_dir / new_filename

        if new_path.exists():
            console.print(f"File already exists: {new_path}", style="yellow")
            if not click.confirm("Overwrite?"):
                return

        # Build new ARB content
        new_arb = {"@@locale": locale_code}

        # Get appropriate plural categories for this locale
        plural_categories = get_plural_categories(locale_code)

        for key, entry in template_entries.items():
            # Mark as untranslated (keep English)
            new_arb[key] = entry.value

            # Copy metadata
            if entry.metadata:
                new_arb[f"@{key}"] = entry.metadata

        # Write new ARB file
        with open(new_path, "w", encoding="utf-8") as f:
            json.dump(new_arb, f, indent=2, ensure_ascii=False)

        console.print(f"✓ Created locale file: {new_path}", style="green")
        console.print(
            f"  Plural categories for {locale_code}: {', '.join(plural_categories)}"
        )
        console.print("\nNext: Translate the strings in the new file", style="dim")

    except Exception as e:
        console.print(f"Error: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    default=None,
    help="Path to l10n.yaml",
)
@click.option(
    "--arb-dir",
    default=None,
    help="ARB directory (overrides config)",
)
def validate(config: Optional[str], arb_dir: Optional[str]):
    """Validate ARB files for syntax and consistency."""
    try:
        # Determine ARB directory
        if arb_dir:
            arb_path = Path(arb_dir)
        elif config:
            l10n_config = L10nConfig.from_yaml(config)
            arb_path = l10n_config.arb_dir
        else:
            try:
                l10n_config = L10nConfig.from_yaml()
                arb_path = l10n_config.arb_dir
            except ConfigurationError:
                console.print(
                    "Error: Specify --arb-dir or create l10n.yaml", style="red"
                )
                sys.exit(1)

        if not arb_path.exists():
            console.print(f"Error: ARB directory not found: {arb_path}", style="red")
            sys.exit(1)

        # Find all ARB files
        arb_files = list(arb_path.glob("*.arb"))
        if not arb_files:
            console.print(f"No ARB files found in {arb_path}", style="yellow")
            return

        console.print(f"Validating {len(arb_files)} ARB file(s)...\n")

        parser = ARBParser()
        errors = []
        warnings = []

        for arb_file in arb_files:
            try:
                parser.parse_file(arb_file)
                validation_issues = parser.validate()

                if validation_issues:
                    warnings.extend(
                        [
                            f"[yellow]{arb_file.name}:[/yellow] {issue}"
                            for issue in validation_issues
                        ]
                    )
                else:
                    console.print(f"✓ {arb_file.name}", style="green")

            except ARBParseError as e:
                errors.append(f"[red]{arb_file.name}:[/red] {e}")

        # Display results
        if errors:
            console.print("\n[bold red]Errors:[/bold red]")
            for error in errors:
                rprint(f"  {error}")

        if warnings:
            console.print("\n[bold yellow]Warnings:[/bold yellow]")
            for warning in warnings:
                rprint(f"  {warning}")

        if not errors and not warnings:
            console.print("\n[bold green]All ARB files are valid![/bold green]")
        elif errors:
            sys.exit(1)

    except Exception as e:
        console.print(f"Error: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    default=None,
    help="Path to l10n.yaml",
)
@click.option(
    "--arb-dir",
    default=None,
    help="ARB directory (overrides config)",
)
def coverage(config: Optional[str], arb_dir: Optional[str]):
    """Show translation coverage statistics."""
    try:
        # Determine ARB directory
        if arb_dir:
            arb_path = Path(arb_dir)
        elif config:
            l10n_config = L10nConfig.from_yaml(config)
            arb_path = l10n_config.arb_dir
        else:
            try:
                l10n_config = L10nConfig.from_yaml()
                arb_path = l10n_config.arb_dir
            except ConfigurationError:
                console.print(
                    "Error: Specify --arb-dir or create l10n.yaml", style="red"
                )
                sys.exit(1)

        # Load translations
        loader = TranslationLoader(arb_path)
        locales = loader.discover_locales()

        if not locales:
            console.print(f"No ARB files found in {arb_path}", style="yellow")
            return

        # Load all translations
        all_keys: set[str] = set()
        locale_translations: dict[str, dict] = {}

        for locale in locales:
            try:
                entries = loader.load_locale(locale)
                locale_translations[locale] = entries
                all_keys.update(entries.keys())
            except Exception:
                pass

        if not all_keys:
            console.print("No translation keys found", style="yellow")
            return

        # Build coverage table
        table = Table(title="Translation Coverage")
        table.add_column("Locale", style="cyan", no_wrap=True)
        table.add_column("Keys", justify="right")
        table.add_column("Coverage", justify="right")
        table.add_column("Missing", justify="right")

        for locale in sorted(locales):
            entries = locale_translations.get(locale, {})
            key_count = len(entries)
            total = len(all_keys)
            coverage = (key_count / total * 100) if total > 0 else 0
            missing = total - key_count

            # Color code based on coverage
            if coverage == 100:
                style = "green"
            elif coverage >= 80:
                style = "yellow"
            else:
                style = "red"

            table.add_row(
                locale,
                str(key_count),
                f"[{style}]{coverage:.1f}%[/{style}]",
                str(missing) if missing > 0 else "-",
            )

        console.print(table)
        console.print(f"\nTotal keys: {len(all_keys)}")

    except Exception as e:
        console.print(f"Error: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option(
    "--config",
    default=None,
    help="Path to l10n.yaml",
)
def watch(config: Optional[str]):
    """Watch ARB files for changes (development mode)."""
    try:
        from .localizations import Localizations
        from .hot_reload import HotReloadWatcher

        console.print("[bold]Starting hot-reload watcher...[/bold]")

        # Load configuration
        if config:
            l10n_config = L10nConfig.from_yaml(config)
        else:
            try:
                l10n_config = L10nConfig.from_yaml()
            except ConfigurationError:
                console.print(
                    "Error: l10n.yaml not found. Run 'flet-l10n init' first.",
                    style="red",
                )
                sys.exit(1)

        console.print(f"Watching: {l10n_config.arb_dir}")
        console.print("Press Ctrl+C to stop\n")

        def on_change(file_path: str):
            console.print(f"[green]✓[/green] Detected change: {Path(file_path).name}")

        watcher = HotReloadWatcher(l10n_config.arb_dir, on_change)

        try:
            watcher.start()
            # Keep running
            import time

            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopping watcher...[/yellow]")
            watcher.stop()
            console.print("[green]Stopped[/green]")

    except Exception as e:
        console.print(f"Error: {e}", style="red")
        sys.exit(1)


@cli.command()
@click.option(
    "--output",
    "-o",
    default="l10n_keys.py",
    help="Output file path (default: l10n_keys.py)",
)
@click.option(
    "--class-name",
    default="L10nKeys",
    help="Name of the generated class (default: L10nKeys)",
)
@click.option(
    "--config",
    "-c",
    default=None,
    help="Path to l10n.yaml configuration file",
)
def generate(output: str, class_name: str, config: Optional[str]):
    """Generate typed keys class from ARB template file."""
    try:
        # Load configuration
        try:
            if config:
                l10n_config = L10nConfig.from_yaml(Path(config))
            else:
                l10n_config = L10nConfig.from_yaml()
        except ConfigurationError as e:
            console.print(f"[red]Error:[/red] {e}")
            console.print(
                "\n[yellow]Hint:[/yellow] Run 'flet-l10n init' to create configuration"
            )
            sys.exit(1)

        # Find template ARB file
        arb_dir = l10n_config.arb_dir
        template_file = None

        if l10n_config.template_arb_file:
            template_file = arb_dir / l10n_config.template_arb_file
        else:
            # Find the first ARB file with default locale
            default_locale = l10n_config.default_locale
            patterns = [
                f"app_{default_locale}.arb",
                f"intl_{default_locale}.arb",
                f"{default_locale}.arb",
            ]
            for pattern in patterns:
                candidate = arb_dir / pattern
                if candidate.exists():
                    template_file = candidate
                    break

        if not template_file or not template_file.exists():
            console.print(f"[red]Error:[/red] Template ARB file not found in {arb_dir}")
            console.print(
                f"[yellow]Looking for:[/yellow] app_{l10n_config.default_locale}.arb"
            )
            sys.exit(1)

        # Generate keys class
        console.print(f"Reading template: {template_file.name}")
        generator = L10nKeysGenerator(template_file)

        output_path = Path(output)
        generator.generate(output_path, class_name)

        console.print(f"[green]✓[/green] Generated: {output_path}")
        console.print(f"[dim]Class name:[/dim] {class_name}")

        # Count generated keys
        parser = ARBParser()
        entries = parser.parse_file(template_file)
        console.print(f"[dim]Total keys:[/dim] {len(entries)}")

        # Show usage example
        rprint("\n[bold]Usage example:[/bold]")
        rprint(f"[dim]from {output_path.stem} import {class_name}[/dim]")
        rprint("")
        rprint(f"[dim]l10n.t({class_name}.appTitle)[/dim]")
        if entries:
            first_key = next(iter(entries.keys()))
            rprint(f"[dim]l10n.t({class_name}.{first_key})[/dim]")

    except Exception as e:
        console.print(f"[red]Error:[/red] {e}", style="red")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    cli()
