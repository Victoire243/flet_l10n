# flet_l10n - Localization for Flet Applications

[![PyPI version](https://badge.fury.io/py/flet-l10n.svg)](https://badge.fury.io/py/flet-l10n)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**flet_l10n** is a Python package that provides localization support for [Flet](https://flet.dev) applications, enabling developers to create multilingual user interfaces with ease. Inspired by Flutter's l10n system, flet_l10n uses ARB (Application Resource Bundle) files and ICU MessageFormat for powerful, flexible translations.

## Features

- **Flutter-Compatible ARB Format** - Use the same translation files as Flutter apps
- **Full CLDR Plural Rules** - Support for 50+ languages with proper pluralization (zero, one, two, few, many, other)
- **Hot-Reload Support** - Automatic translation reload during development
- **Type-Safe API** - Full type hints for excellent IDE support
- **Lazy Loading** - Translations are loaded only when needed
- **Dual Integration Patterns** - Global singleton or context-based providers with callback system
- **CLI Tools** - Project scaffolding, validation, and coverage reports
- **Auto-Locale Detection** - Automatically detect system locale on startup
- **Compiled Pattern Caching** - Optimized performance with LRU cache
- **Update Callbacks** - Automatic UI updates on locale change

## Installation

```bash
pip install flet-l10n
```

## Quick Start

### 1. Initialize Your Project

```bash
flet-l10n init
```

This creates:
- `l10n.yaml` - Configuration file
- `locales/app_en.arb` - Template ARB file with examples

### 2. Add More Locales

```bash
flet-l10n add-locale fr
flet-l10n add-locale es
```

### 3. Use in Your Flet App

#### Global Pattern (Simple)

```python
import flet as ft
from flet_l10n import Localizations
from l10n_keys import L10nKeys # Assume you generate this file with "flet-l10n generate" command


# Initialize once
l10n = Localizations.from_config()

def main(page: ft.Page):
    page.title = "flet_l10n Example"

    # Create UI components
    title = ft.Text(size=24, weight=ft.FontWeight.BOLD)
    welcome = ft.Text(size=18)
    items = ft.Text(size=16)

    # Define update function
    def update_ui():
        title.value = l10n.t(L10nKeys.appTitle)
        welcome.value = l10n.t(L10nKeys.welcome, name="Victoire")
        items.value = l10n.plural(L10nKeys.itemCount, count=5)
        page.update()

    # Register callback for locale changes
    l10n.on_locale_change(lambda _: update_ui())

    # Language switcher
    def change_language(e):
        l10n.set_locale(e.control.value)
        # update_ui() will be called automatically

    dropdown = ft.Dropdown(
        options=[
            ft.dropdown.Option("en", "English en"),
            ft.dropdown.Option("es", "Español es"),
            ft.dropdown.Option("fr", "Français fr"),
        ],
        value=l10n.current_locale,
        on_select=change_language,
        width=200,
    )

    # Initial update
    update_ui()

    page.add(
        title,
        welcome,
        items,
        ft.Divider(height=20),
        dropdown,
    )

ft.run(main)
```

#### Context-Based Pattern (Flet-Style)

```python
"""Example demonstrating context-based provider pattern with proper UI updates."""

import flet as ft
from flet_l10n import LocalizationsProvider, use_localizations
from l10n_keys import L10nKeys # Assume you generate this file with "flet-l10n generate" command


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
            ft.dropdown.Option("en", "English"),
            ft.dropdown.Option("es", "Español"),
            ft.dropdown.Option("fr", "Français"),
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
        title.value = l10n.t(L10nKeys.appTitle)
        welcome.value = l10n.t(L10nKeys.welcome, name="Victoire")
        item_count.value = l10n.plural(
            L10nKeys.itemCount, count=int(count_slider.value)
        )
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
        item_count.value = l10n.plural(L10nKeys.itemCount, count=int(e.control.value))
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
                                "How it works:", size=14, weight=ft.FontWeight.BOLD
                            ),
                            ft.Text(
                                "Change language → All components update automatically",
                                size=12,
                            ),
                            ft.Text(
                                "Uses callback pattern for imperative updates",
                                size=12,
                            ),
                            ft.Text(
                                "No need to manually refresh each component", size=12
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

```

**Important:** With the context-based pattern, you must:
1. Register an `update_ui()` callback with `provider.add_update_callback()`
2. This callback will be called automatically when locale changes
3. Update all component values in the callback

See [examples/](examples/) for complete working examples with both imperative and rebuild patterns.

## Configuration (l10n.yaml)

```yaml
arb-dir: locales
default-locale: en
fallback-locale: en
template-arb-file: app_en.arb
hot-reload: true
supported-locales:
  - en
  - es
  - fr
```

## ARB File Format

ARB files are JSON files with translation strings and metadata:

```json
{
  "@@locale": "en",
  "appTitle": "My Application",
  "@appTitle": {
    "description": "The title of the application"
  },
  "welcome": "Welcome, {name}!",
  "@welcome": {
    "description": "Welcome message",
    "placeholders": {
      "name": {
        "type": "String",
        "example": "Victoire"
      }
    }
  },
  "itemCount": "{count, plural, =0{No items} one{One item} other{{count} items}}",
  "@itemCount": {
    "description": "Item count with pluralization",
    "placeholders": {
      "count": {
        "type": "int"
      }
    }
  },
  "gender": "{gender, select, male{He} female{She} other{They}} likes this",
  "@gender": {
    "description": "Gender-based selection"
  }
}
```

## ICU MessageFormat Examples

### Simple Placeholders

```json
{
  "greeting": "Hello, {name}!"
}
```

```python
l10n.t("greeting", name="Alice")  # "Hello, Alice!"
```

or

```python
l10n.translate(L10nKeys.greeting, name="Alice")  # After generating l10n_keys.py file with "flet-l10n generate" command
```

### Pluralization (CLDR Rules)

```json
{
  "messages": "{count, plural, =0{No messages} one{One message} other{{count} messages}}"
}
```

```python
l10n.plural("messages", count=0)   # "No messages"
l10n.plural("messages", count=1)   # "One message"
l10n.plural("messages", count=5)   # "5 messages"
```

or

```python
# After generating l10n_keys.py file with "flet-l10n generate" command
l10n.plural(L10nKeys.messages, count=0)  # "No messages"
l10n.plural(L10nKeys.messages, count=1)  # "One message"
l10n.plural(L10nKeys.messages, count=5)  # "5 messages" 
```

### Select (Choice)

```json
{
  "preference": "{choice, select, coffee{I like coffee} tea{I like tea} other{I like water}}"
}
```

```python
l10n.t("preference", choice="coffee")  # "I like coffee"
```

or

```python
# After generating l10n_keys.py file with "flet-l10n generate" command
l10n.t(L10nKeys.preference, choice="coffee")  # "I like coffee"
```

## CLI Commands

### Initialize Project

```bash
flet-l10n init
flet-l10n init --arb-dir translations --default-locale fr
```

### Add New Locale

```bash
flet-l10n add-locale es
flet-l10n add-locale de --from-template locales/app_en.arb
```

### Validate ARB Files

```bash
flet-l10n validate
flet-l10n validate --arb-dir locales
```

### Show Translation Coverage

```bash
flet-l10n coverage
```

Output:

```bash
        Translation Coverage
┏━━━━━━━━┳━━━━━━┳━━━━━━━━━━┳━━━━━━━━━┓
┃ Locale ┃ Keys ┃ Coverage ┃ Missing ┃
┡━━━━━━━━╇━━━━━━╇━━━━━━━━━━╇━━━━━━━━━┩
│ en     │    3 │   100.0% │       - │
│ es     │    3 │   100.0% │       - │
│ fr     │    3 │   100.0% │       - │
└────────┴──────┴──────────┴─────────┘

Total keys: 3
```

### Watch for Changes (Development)

```bash
flet-l10n watch
```

### Generate Typed Keys Class

Generate a Python class with typed constants for all your translation keys. This enables IDE autocompletion and prevents typos:

```bash
flet-l10n generate
flet-l10n generate --output l10n_keys.py --class-name L10nKeys
```

This creates a file like:

```python
class L10nKeys:
    """Typed keys for localization strings."""
    
    # The title of the application
    appTitle = "appTitle"
    
    # Welcome message with user name
    # Placeholders: name
    welcome = "welcome"
    
    # Display item count with pluralization
    # Placeholders: count
    itemCount = "itemCount"
```

Use it in your code:

```python
from l10n_keys import L10nKeys

# IDE will autocomplete L10nKeys.appTitle, L10nKeys.welcome, etc.
page.title = l10n.t(L10nKeys.appTitle)
greeting = l10n.t(L10nKeys.welcome, name="Victoire")
```

Benefits:
- **IDE Autocompletion** - Get suggestions for all available keys
- **Type Safety** - Catch typos at edit time, not runtime
- **Documentation** - Docstrings show descriptions and placeholders
- **Refactoring Support** - Rename keys with confidence

## API Reference

### Localizations Class

```python
# Initialize from config
l10n = Localizations.from_config("l10n.yaml")

# Initialize manually
l10n = Localizations(
    arb_dir="locales",
    default_locale="en",
    fallback_locale="en",
    hot_reload=True
)

# Translate
l10n.t("key", placeholder="value")
l10n.translate("key", placeholder="value")

# Plural
l10n.plural("key", count=5)

# Change locale
l10n.set_locale("es")

# Get current locale
current = l10n.current_locale

# Check if key exists
exists = l10n.has_key("someKey")

# Get all keys
keys = l10n.get_all_keys()

# Reload translations
l10n.reload_translations()

# Enable/disable hot-reload
l10n.enable_hot_reload()
l10n.disable_hot_reload()

# Register locale change callback
l10n.on_locale_change(lambda locale: print(f"Changed to {locale}"))
```

### Context-Based Provider

```python
from flet_l10n import LocalizationsProvider, use_localizations

# Initialize provider
provider = LocalizationsProvider(page, arb_dir="locales")

# Access localization
l10n = use_localizations(page)

# Register update callback (REQUIRED for UI updates)
def update_ui():
    # Update your components here
    title.value = l10n.t("appTitle")
    page.update()

provider.add_update_callback(update_ui)

# Change locale (update_ui will be called automatically)
l10n.set_locale("es")

# Remove callback when no longer needed
provider.remove_update_callback(update_ui)
```

**Two Update Patterns:**

1. **Imperative** (Recommended for complex UIs):
   ```python
   # Update specific components
   def update_ui():
       title.value = l10n.t("appTitle")
       welcome.value = l10n.t("welcome", name="User")
       page.update()
   ```

2. **Rebuild** (Simpler for small apps):
   ```python
   # Rebuild entire UI
   def rebuild_ui():
       page.clean()
       page.add(build_ui())
       page.update()
   ```

## Supported Languages (CLDR Plural Rules)

flet_l10n includes CLDR plural rules for 50+ languages including:

- **Germanic**: English, German, Dutch, Swedish, Danish, Norwegian
- **Romance**: French, Spanish, Italian, Portuguese, Romanian
- **Slavic**: Russian, Polish, Czech, Slovak, Ukrainian, Serbian
- **Arabic**: Full 6-form plurals (zero, one, two, few, many, other)
- **Asian**: Chinese, Japanese, Korean (no plural distinction)
- **Others**: Turkish, Finnish, Hungarian, Hebrew, Greek, and more

## Understanding Component Updates with Flet

### Why Callbacks Are Needed

In Flet, UI components don't automatically re-evaluate their values when data changes. When you change the locale, your components (Text, Button, etc.) still have their old values. There are two approaches:

#### 1. Imperative Pattern (Recommended)

Explicitly update each component's value:

```python
def update_ui():
    """Called automatically when locale changes."""
    title.value = l10n.t("appTitle")
    welcome.value = l10n.t("welcome", name="User")
    page.update()

provider.add_update_callback(update_ui)
```

**Advantages:**
- ✅ Efficient - only updates necessary components
- ✅ Fine control - update only what changed
- ✅ Best for complex UIs with many components

**Example:** See [examples/provider_example.py](examples/provider_example.py)

#### 2. Rebuild Pattern (Simpler)

Reconstruct the entire UI:

```python
def rebuild_ui():
    """Rebuild entire page on locale change."""
    page.clean()
    page.add(build_ui())
    page.update()

provider.add_update_callback(rebuild_ui)
```

**Advantages:**
- ✅ Simple - no manual component tracking
- ✅ Less code - one function rebuilds everything
- ✅ Good for small/simple apps

**Disadvantages:**
- ⚠️ Less efficient - recreates all components
- ⚠️ Loses component state (scroll position, input values, etc.)

**Example:** See [examples/provider_rebuild_example.py](examples/provider_rebuild_example.py)

### Complete Working Example

```python
import flet as ft
from flet_l10n import LocalizationsProvider, use_localizations

def main(page: ft.Page):
    page.title = "Language Switcher"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # Initialize provider
    provider = LocalizationsProvider(page, config_path="l10n.yaml")
    l10n = use_localizations(page)
    
    # Create components
    title = ft.Text(size=32, weight=ft.FontWeight.BOLD)
    welcome = ft.Text(size=20)
    item_slider = ft.Slider(min=0, max=10, value=3, divisions=10, label="{value}")
    item_count = ft.Text(size=16)
    
    # Update function
    def update_ui():
        title.value = l10n.t("appTitle")
        welcome.value = l10n.t("welcome", name="World")
        item_count.value = l10n.plural("itemCount", count=int(item_slider.value))
        dropdown.value = l10n.current_locale
        page.update()
    
    # Register callback
    provider.add_update_callback(update_ui)
    
    # Slider change handler
    def on_slider_change(e):
        item_count.value = l10n.plural("itemCount", count=int(e.control.value))
        page.update()
    
    item_slider.on_change = on_slider_change
    
    # Language dropdown
    dropdown = ft.Dropdown(
        label="Select Language",
        options=[
            ft.dropdown.Option("en", "English 🇬🇧"),
            ft.dropdown.Option("es", "Español 🇪🇸"),
            ft.dropdown.Option("fr", "Français 🇫🇷"),
        ],
        on_select=lambda e: l10n.set_locale(e.control.value),
        width=250,
    )
    
    # Initial update
    update_ui()
    
    # Build UI
    page.add(
        ft.Container(
            content=ft.Column([
                title,
                welcome,
                ft.Divider(height=20),
                ft.Text("Items:", size=14),
                item_slider,
                item_count,
                ft.Divider(height=20),
                dropdown,
            ], spacing=10),
            padding=30,
        )
    )

ft.run(main)
```

### Migration from Old Pattern

If you have code that doesn't use callbacks:

**❌ Old (doesn't work):**
```python
def change_language(e):
    l10n.set_locale(e.control.value)
    page.update()  # Components still have old values!
```

**✅ New (works correctly):**
```python
# Register callback once
def update_ui():
    title.value = l10n.t("appTitle")
    welcome.value = l10n.t("welcome")
    page.update()

provider.add_update_callback(update_ui)

# Now locale changes trigger update_ui automatically
def change_language(e):
    l10n.set_locale(e.control.value)
```

## Advanced Features

### Locale Fallback Chain

```python
# If locale "en-GB" is not found, flet_l10n will try:
# 1. en-GB (exact match)
# 2. en (language only)
# 3. Fallback locale (configured)
l10n.set_locale("en-GB")
```

### Custom Locale Detection

```python
import locale

# Auto-detect on init
l10n = Localizations(arb_dir="locales", auto_detect_locale=True)

# Manual detection
system_locale = locale.getdefaultlocale()[0]
l10n.set_locale(system_locale)
```

### Hot-Reload with Callbacks

```python
def on_translation_change(file_path):
    print(f"Translations updated: {file_path}")
    page.update()

l10n.enable_hot_reload(callback=on_translation_change)
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Credits

Inspired by:
- [Flutter's l10n system](https://docs.flutter.dev/development/accessibility-and-localization/internationalization)
- [ARB format specification](https://github.com/google/app-resource-bundle)
- [ICU MessageFormat](https://unicode-org.github.io/icu/userguide/format_parse/messages/)
- [CLDR Plural Rules](https://www.unicode.org/cldr/charts/latest/supplemental/language_plural_rules.html)

## Support

- [Documentation](https://github.com/Victoire243/flet_l10n)
- [Issue Tracker](https://github.com/Victoire243/flet_l10n/issues)
- [Discussions](https://github.com/Victoire243/flet_l10n/discussions)
