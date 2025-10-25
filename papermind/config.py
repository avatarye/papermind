"""Configuration management for Papermind."""

import os
import json
from pathlib import Path
from typing import Optional, Dict, Any


class Config:
    """
    Manages persistent configuration for Papermind.

    Configuration is stored in the user's home directory:
    - Windows: %USERPROFILE%/.papermind/config.json
    - Linux/Mac: ~/.papermind/config.json
    """

    def __init__(self):
        """Initialize configuration manager."""
        self.config_dir = Path.home() / ".papermind"
        self.config_file = self.config_dir / "config.json"
        self._config: Dict[str, Any] = {}
        self._load()

    def _load(self) -> None:
        """Load configuration from disk."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                # If config is corrupted, start fresh
                self._config = {}

    def _save(self) -> None:
        """Save configuration to disk."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self._config, f, indent=2)

    def is_configured(self) -> bool:
        """Check if basic configuration exists."""
        return bool(self.get_zotero_path() and self.get_api_key())

    def get_obsidian_vault_path(self) -> Optional[str]:
        """Get configured Obsidian vault path."""
        return self._config.get('obsidian_vault_path')

    def set_obsidian_vault_path(self, path: str) -> None:
        """Set Obsidian vault path."""
        # Validate path exists
        if not Path(path).exists():
            raise ValueError(f"Path does not exist: {path}")
        if not Path(path).is_dir():
            raise ValueError(f"Path is not a directory: {path}")

        self._config['obsidian_vault_path'] = str(path)
        self._save()

    def get_zotero_path(self) -> Optional[str]:
        """Get configured Zotero path."""
        return self._config.get('zotero_path')

    def set_zotero_path(self, path: str) -> None:
        """Set Zotero path."""
        # Validate path exists
        if not Path(path).exists():
            raise ValueError(f"Path does not exist: {path}")
        if not (Path(path) / "zotero.sqlite").exists():
            raise ValueError(f"No zotero.sqlite found in: {path}")

        self._config['zotero_path'] = str(path)
        self._save()

    def get_api_key(self) -> Optional[str]:
        """
        Get Claude API key.

        Priority:
        1. Environment variable ANTHROPIC_API_KEY
        2. Configured value in config file
        """
        # Check environment first
        env_key = os.getenv('ANTHROPIC_API_KEY')
        if env_key:
            return env_key

        return self._config.get('api_key')

    def set_api_key(self, api_key: str) -> None:
        """Set Claude API key."""
        if not api_key or not api_key.startswith('sk-ant-'):
            raise ValueError("Invalid API key format")

        self._config['api_key'] = api_key
        self._save()

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self._config.copy()

    def clear(self) -> None:
        """Clear all configuration."""
        self._config = {}
        if self.config_file.exists():
            self.config_file.unlink()


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config
