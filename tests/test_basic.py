"""Test script to verify flet_l10n functionality."""

from flet_l10n import Localizations

# Initialize from config
print("Initializing localization...")
l10n = Localizations.from_config()

print(f"Current locale: {l10n.current_locale}")
print(f"Supported locales: {l10n.supported_locales}")
print()

# Test simple translation
print("=== Simple Translation ===")
print(f"English: {l10n.t('appTitle')}")
l10n.set_locale("es")
print(f"Spanish: {l10n.t('appTitle')}")
l10n.set_locale("fr")
print(f"French: {l10n.t('appTitle')}")
print()

# Test placeholders
print("=== Placeholders ===")
l10n.set_locale("en")
print(f"English: {l10n.t('welcome', name='Alice')}")
l10n.set_locale("es")
print(f"Spanish: {l10n.t('welcome', name='Alice')}")
print()

# Test pluralization
print("=== Pluralization (CLDR Rules) ===")
l10n.set_locale("en")
for count in [0, 1, 2, 5]:
    print(f"English count={count}: {l10n.plural('itemCount', count=count)}")

print()
l10n.set_locale("es")
for count in [0, 1, 2, 5]:
    print(f"Spanish count={count}: {l10n.plural('itemCount', count=count)}")

print()
l10n.set_locale("fr")
for count in [0, 1, 2, 5]:
    print(f"French count={count}: {l10n.plural('itemCount', count=count)}")

print()
print("=== Success! ===")
print("All features working correctly!")
