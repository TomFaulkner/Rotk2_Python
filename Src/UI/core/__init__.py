"""
UI Framework Core Package

Base classes and utilities for the ROTK2 UI system.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .component import UIComponent
    from .container import UIContainer
    from .manager import UIManager


class Anchor(Enum):
    """Position anchor points for UI components."""

    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    CENTER_LEFT = "center_left"
    CENTER = "center"
    CENTER_RIGHT = "center_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


class Alignment(Enum):
    """Alignment for layouts."""

    START = auto()
    CENTER = auto()
    END = auto()
    STRETCH = auto()


class FocusDirection(Enum):
    """Direction for focus navigation."""

    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    NEXT = auto()
    PREVIOUS = auto()


class InputMode(Enum):
    """Input mode for UI."""

    AUTO = auto()  # Automatically detect based on last input
    MOUSE = auto()  # Mouse/touch primary
    KEYBOARD = auto()  # Keyboard navigation
    GAMEPAD = auto()  # Gamepad/controller


class UIMode(Enum):
    """UI display mode."""

    CLASSIC = "classic"  # 640x400 EGA style
    MODERN = "modern"  # 1280x800 Steam Deck optimized
