"""
ROTK2 Battle System Configuration

Centralized configuration management using Pydantic Settings.
Supports environment variables from .env file.
"""

from enum import Enum
from pydantic_settings import BaseSettings, SettingsConfigDict


class Language(str, Enum):
    """Supported game languages."""

    CHINESE = "zh"
    ENGLISH = "en"


class RiceDepletionMode(str, Enum):
    """How to handle rice depletion in battles."""

    FORCE_RETREAT = "force_retreat"  # Original game behavior - force full retreat
    DESERTION = "desertion"  # Alternative - 15% troop desertion


class UIMode(str, Enum):
    """UI mode for the game."""

    CLASSIC = "classic"  # Original DOS CGA-style UI
    MODERN = "modern"  # New Steam Deck optimized UI


class BattleSettings(BaseSettings):
    """
    Battle system configuration settings.

    All settings can be overridden via environment variables
    or in the .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Allow extra env vars without errors
    )

    # UI mode setting (controls which UI system to use)
    ui_mode: UIMode = UIMode.MODERN
    """UI mode: 'classic' (DOS-style) or 'modern' (Steam Deck optimized)"""

    # Language setting
    language: Language = Language.CHINESE
    """Game language: 'zh' for Chinese, 'en' for English"""

    # Rice consumption settings
    rice_depletion_mode: RiceDepletionMode = RiceDepletionMode.FORCE_RETREAT
    """Behavior when rice runs out: 'force_retreat' (original) or 'desertion' (alternative)"""

    rice_consumption_rate: int = 250
    """Troops per rice unit (default: 250 troops = 1 rice)"""

    desertion_percentage: float = 0.15
    """Percentage of troops that desert when rice runs out (only for desertion mode)"""

    # Battle mechanics settings
    max_battle_days: int = 30
    """Maximum number of days a battle can last"""

    max_units_on_map: int = 10
    """Maximum units allowed on battlefield per side"""

    # Debug settings
    debug_mode: bool = False
    """Enable debug logging"""

    log_battle_events: bool = True
    """Log battle events to console"""


# Global settings instance
_settings: BattleSettings | None = None


def get_settings() -> BattleSettings:
    """
    Get the global settings instance.

    Returns:
        BattleSettings instance
    """
    global _settings
    if _settings is None:
        _settings = BattleSettings()
    return _settings


def reload_settings() -> BattleSettings:
    """
    Reload settings from environment/.env file.

    Returns:
        Updated BattleSettings instance
    """
    global _settings
    _settings = BattleSettings()
    return _settings


# Convenience exports
RICE_DEPLETION_RETREAT = RiceDepletionMode.FORCE_RETREAT
RICE_DEPLETION_DESERTION = RiceDepletionMode.DESERTION
LANGUAGE_CHINESE = Language.CHINESE
LANGUAGE_ENGLISH = Language.ENGLISH
UI_MODE_CLASSIC = UIMode.CLASSIC
UI_MODE_MODERN = UIMode.MODERN
