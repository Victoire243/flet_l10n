"""Simple test to verify typed keys work correctly."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flet_l10n import Localizations
from l10n_keys import L10nKeys


def test_typed_keys():
    """Test that typed keys work correctly."""
    # Initialize localizations
    l10n = Localizations.from_config()

    print("Testing typed keys with camelCase format:")
    print("=" * 50)

    # Test 1: Simple translation with typed key
    print(f"\n1. L10nKeys.appTitle = '{L10nKeys.appTitle}'")
    print(f"   Translation: {l10n.t(L10nKeys.appTitle)}")

    # Test 2: Translation with placeholder
    print(f"\n2. L10nKeys.welcome = '{L10nKeys.welcome}'")
    print(f"   Translation: {l10n.t(L10nKeys.welcome, name='Bob')}")

    # Test 3: Plural translation
    print(f"\n3. L10nKeys.itemCount = '{L10nKeys.itemCount}'")
    print(f"   Translation (0): {l10n.t(L10nKeys.itemCount, count=0)}")
    print(f"   Translation (1): {l10n.t(L10nKeys.itemCount, count=1)}")
    print(f"   Translation (5): {l10n.t(L10nKeys.itemCount, count=5)}")

    # Test 4: Get all keys
    print(f"\n4. All keys: {L10nKeys.all_keys()}")

    # Test 5: Switch locales
    print("\n5. Testing locale switching:")
    for locale in ["en", "es", "fr"]:
        l10n.set_locale(locale)
        print(
            f"   [{locale}] {l10n.t(L10nKeys.appTitle)}: {l10n.t(L10nKeys.welcome, name='User')}"
        )

    print("\n" + "=" * 50)
    print("âœ… All typed keys tests passed!")
    print("\nBenefits of using typed keys:")
    print("  - IDE autocomplete for L10nKeys.appTitle, L10nKeys.welcome, etc.")
    print("  - Catch typos at edit time (not runtime)")
    print("  - Jump to definition support")
    print("  - Refactoring-friendly")


if __name__ == "__main__":
    test_typed_keys()
