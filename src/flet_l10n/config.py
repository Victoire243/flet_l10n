"""Configuration management for flet_l10n using l10n.yaml."""

import os
from pathlib import Path
from typing import Any

import yaml

from .exceptions import ConfigurationError


class L10nConfig:
    """Configuration for localization loaded from l10n.yaml."""

    def __init__(
        self,
        arb_dir: str | Path = "locales",
        default_locale: str = "en",
        fallback_locale: str | None = None,
        supported_locales: list[str] | None = None,
        template_arb_file: str | None = None,
        hot_reload: bool = False,
    ):
        """Initialize localization configuration.

        Args:
            arb_dir: Directory containing ARB files
            default_locale: Default locale to use (auto-detected from system if not set)
            fallback_locale: Fallback locale when translation is missing
            supported_locales: List of supported locales (auto-detected from ARB files if not set)
            template_arb_file: Name of the template ARB file (e.g., 'app_en.arb')
            hot_reload: Enable hot-reload during development
        """
        self.arb_dir = Path(arb_dir)
        self.default_locale = default_locale
        self.fallback_locale = fallback_locale or default_locale
        self.supported_locales = supported_locales or []
        self.template_arb_file = template_arb_file
        self.hot_reload = hot_reload

    @classmethod
    def from_yaml(cls, config_path: str | Path | None = None) -> "L10nConfig":
        """Load configuration from l10n.yaml file.

        Args:
            config_path: Path to l10n.yaml file. If None, searches for it in current directory
                        and parent directories.

        Returns:
            L10nConfig instance

        Raises:
            ConfigurationError: If configuration file is invalid or not found
        """
        if config_path is None:
            config_path = cls._find_config_file()
        else:
            config_path = Path(config_path)

        if not config_path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigurationError(f"Invalid YAML in {config_path}: {e}")
        except Exception as e:
            raise ConfigurationError(f"Error reading {config_path}: {e}")

        # Convert kebab-case to snake_case for Python
        config_dict = {
            "arb_dir": data.get("arb-dir", "locales"),
            "default_locale": data.get("default-locale", "en"),
            "fallback_locale": data.get("fallback-locale"),
            "supported_locales": data.get("supported-locales"),
            "template_arb_file": data.get("template-arb-file"),
            "hot_reload": data.get("hot-reload", False),
        }

        # Resolve arb_dir relative to config file location
        arb_dir = Path(config_dict["arb_dir"])
        if not arb_dir.is_absolute():
            arb_dir = config_path.parent / arb_dir
        config_dict["arb_dir"] = arb_dir

        return cls(**config_dict)

    @staticmethod
    def _find_config_file() -> Path:
        """Find l10n.yaml in current directory or parent directories.

        Returns:
            Path to l10n.yaml file

        Raises:
            ConfigurationError: If configuration file is not found
        """
        current_dir = Path.cwd()

        # Search up to 5 levels up
        for _ in range(5):
            config_path = current_dir / "l10n.yaml"
            if config_path.exists():
                return config_path

            # Try parent directory
            parent = current_dir.parent
            if parent == current_dir:  # Reached root
                break
            current_dir = parent

        raise ConfigurationError(
            "l10n.yaml not found in current directory or parent directories. "
            "Run 'flet-l10n init' to create one."
        )

    def validate(self) -> None:
        """Validate configuration.

        Raises:
            ConfigurationError: If configuration is invalid
        """
        if not self.arb_dir.exists():
            raise ConfigurationError(f"ARB directory not found: {self.arb_dir}")

        if not self.arb_dir.is_dir():
            raise ConfigurationError(f"ARB path is not a directory: {self.arb_dir}")

        if not self.default_locale:
            raise ConfigurationError("default-locale cannot be empty")

        if not self.fallback_locale:
            raise ConfigurationError("fallback-locale cannot be empty")

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary for serialization.

        Returns:
            Dictionary with kebab-case keys for YAML output
        """
        return {
            "arb-dir": str(self.arb_dir),
            "default-locale": self.default_locale,
            "fallback-locale": self.fallback_locale,
            "supported-locales": (
                self.supported_locales if self.supported_locales else None
            ),
            "template-arb-file": self.template_arb_file,
            "hot-reload": self.hot_reload,
        }
