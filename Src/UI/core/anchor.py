"""
Anchor and positioning system for UI components.

Provides flexible positioning relative to parent containers.
"""

from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


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


class Position:
    """
    Flexible position specification.

    Can be absolute pixels, relative percentage, or anchored.

    Examples:
        Position(100, 200)                    # Absolute: 100px, 200px
        Position("10%", "20%")                # Relative: 10% of width, 20% of height
        Position(0, 0, anchor=Anchor.CENTER)  # Centered
    """

    def __init__(
        self, x: int | float | str, y: int | float | str, anchor: Anchor = Anchor.TOP_LEFT
    ):
        """
        Initialize position.

        Args:
            x: X coordinate (int/float for pixels, str with % for relative)
            y: Y coordinate (int/float for pixels, str with % for relative)
            anchor: Anchor point for positioning
        """
        self._x = x
        self._y = y
        self.anchor = anchor

    @property
    def x(self) -> int | float | str:
        """Get X coordinate specification."""
        return self._x

    @property
    def y(self) -> int | float | str:
        """Get Y coordinate specification."""
        return self._y

    def resolve(self, parent_size: tuple[int, int], own_size: tuple[int, int]) -> tuple[int, int]:
        """
        Resolve position to absolute coordinates.

        Args:
            parent_size: Size of parent container (width, height)
            own_size: Size of this component (width, height)

        Returns:
            Absolute (x, y) coordinates
        """
        # Resolve X
        if isinstance(self._x, str) and self._x.endswith("%"):
            x = int(parent_size[0] * float(self._x[:-1]) / 100)
        else:
            x = int(self._x)

        # Resolve Y
        if isinstance(self._y, str) and self._y.endswith("%"):
            y = int(parent_size[1] * float(self._y[:-1]) / 100)
        else:
            y = int(self._y)

        # Apply anchor adjustment
        x, y = self._apply_anchor(x, y, own_size)

        return (x, y)

    def _apply_anchor(self, x: int, y: int, own_size: tuple[int, int]) -> tuple[int, int]:
        """Adjust position based on anchor point."""
        w, h = own_size

        anchor_adjustments = {
            Anchor.TOP_LEFT: (0, 0),
            Anchor.TOP_CENTER: (-w // 2, 0),
            Anchor.TOP_RIGHT: (-w, 0),
            Anchor.CENTER_LEFT: (0, -h // 2),
            Anchor.CENTER: (-w // 2, -h // 2),
            Anchor.CENTER_RIGHT: (-w, -h // 2),
            Anchor.BOTTOM_LEFT: (0, -h),
            Anchor.BOTTOM_CENTER: (-w // 2, -h),
            Anchor.BOTTOM_RIGHT: (-w, -h),
        }

        dx, dy = anchor_adjustments.get(self.anchor, (0, 0))
        return (x + dx, y + dy)

    def __repr__(self) -> str:
        return f"Position({self._x!r}, {self._y!r}, anchor={self.anchor.value!r})"
