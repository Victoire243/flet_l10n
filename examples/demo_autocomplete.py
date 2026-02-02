"""Quick demo of typed keys autocomplete feature."""

from flet_l10n import Localizations
from l10n_keys import L10nKeys

# Initialize
l10n = Localizations.from_config()

# Old way (string literals - typos possible):
# title = l10n.t("appTitle")
# greeting = l10n.t("welcom")  # âš ï¸ Typo! Only found at runtime

# New way (typed keys - IDE autocomplete):
# When you type L10nKeys. your IDE shows:
#   - appTitle
#   - welcome
#   - itemCount
title = l10n.t(L10nKeys.appTitle)
greeting = l10n.t(L10nKeys.welcome, name="Developer")
items = l10n.t(L10nKeys.itemCount, count=3)

print("=== Typed Keys Demo ===")
print(f"Title: {title}")
print(f"Greeting: {greeting}")
print(f"Items: {items}")
print("\nâœ… Try typing 'L10nKeys.' in your IDE to see autocompletion!")
