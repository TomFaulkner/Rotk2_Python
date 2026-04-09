"""
Base UI component class.

All UI elements inherit from UIComponent.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable

import pygame

if TYPE_CHECKING:
    from .anchor import Anchor, Position
    from .transform import Transform


class UIComponent(ABC):
    """
    Base class for all UI components.

    This is an abstract base class that defines the interface for all
    UI elements. Components have position, size, visibility, and can
    handle input events.

    Attributes:
        visible: Whether the component is visible
        enabled: Whether the component accepts input
        parent: Parent container (if any)
        anchor: Positioning anchor
    """

    def __init__(
        self,
        position: tuple[int | float | str, int | float | str] | Position = (0, 0),
        size: tuple[int, int] | None = None,
        anchor: Anchor | None = None,
        parent: UIContainer | None = None,
    ):
        """
        Initialize UI component.

        Args:
            position: Position as (x, y) tuple or Position object
            size: Size as (width, height) tuple, or None for auto-size
            anchor: Positioning anchor, or None for TOP_LEFT
            parent: Parent container, or None for root
        """
        from .anchor import Anchor, Position

        # Handle position
        if isinstance(position, tuple):
            self._position = Position(position[0], position[1], anchor or Anchor.TOP_LEFT)
        else:
            self._position = position

        self._size = size or (100, 30)
        self._anchor = anchor or Anchor.TOP_LEFT
        self.parent = parent

        # State
        self.visible = True
        self.enabled = True
        self.focused = False

        # Cached calculated values
        self._virtual_rect = pygame.Rect(0, 0, 0, 0)
        self._screen_rect = pygame.Rect(0, 0, 0, 0)
        self._needs_recalculate = True

        # Callbacks
        self.on_focus: Callable[[], None] | None = None
        self.on_blur: Callable[[], None] | None = None
        self.on_click: Callable[[], None] | None = None

        if parent:
            parent.add_child(self)

    @property
    def position(self) -> Position:
        """Get position specification."""
        return self._position

    @position.setter
    def position(self, value: tuple[int | float | str, int | float | str] | Position) -> None:
        """Set position specification."""
        from .anchor import Position

        if isinstance(value, tuple):
            self._position = Position(value[0], value[1], self._anchor)
        else:
            self._position = value
        self._needs_recalculate = True

    @property
    def size(self) -> tuple[int, int]:
        """Get size."""
        return self._size

    @size.setter
    def size(self, value: tuple[int, int]) -> None:
        """Set size."""
        self._size = value
        self._needs_recalculate = True

    @property
    def rect(self) -> pygame.Rect:
        """Get rectangle in virtual coordinates."""
        if self._needs_recalculate:
            self._recalculate_rect()
        return self._virtual_rect

    def _recalculate_rect(self) -> None:
        """Recalculate virtual rectangle from position and size."""
        parent_size = self._get_parent_size()
        x, y = self._position.resolve(parent_size, self._size)
        self._virtual_rect = pygame.Rect(x, y, self._size[0], self._size[1])
        self._needs_recalculate = False

    def _get_parent_size(self) -> tuple[int, int]:
        """Get parent container size."""
        if self.parent:
            return self.parent.size
        # Default to modern mode resolution
        return (1280, 800)

    def invalidate(self) -> None:
        """Mark component as needing recalculation."""
        self._needs_recalculate = True

    def set_visible(self, visible: bool) -> None:
        """Set visibility."""
        self.visible = visible

    def set_enabled(self, enabled: bool) -> None:
        """Set enabled state."""
        self.enabled = enabled

    def set_focus(self, focused: bool) -> None:
        """Set focus state."""
        if self.focused == focused:
            return

        self.focused = focused
        if focused and self.on_focus:
            self.on_focus()
        elif not focused and self.on_blur:
            self.on_blur()

    def contains_point(self, point: tuple[int, int], transform: Transform) -> bool:
        """
        Check if screen point is inside component.

        Args:
            point: Screen coordinates (x, y)
            transform: Transform for coordinate conversion

        Returns:
            True if point is inside component
        """
        if not self.visible:
            return False

        # Use absolute position for correct hit detection with nested containers
        abs_x, abs_y = self.get_absolute_position()
        abs_rect = pygame.Rect(abs_x, abs_y, self._size[0], self._size[1])
        screen_rect = transform.to_screen(abs_rect)
        return screen_rect.collidepoint(point)

    def handle_event(self, event: pygame.event.Event, transform: Transform) -> bool:
        """
        Handle input event.

        Args:
            event: Pygame event
            transform: Transform for coordinate conversion

        Returns:
            True if event was consumed, False to propagate
        """
        if not self.enabled or not self.visible:
            return False

        # Convert mouse events to virtual coordinates
        if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
            virtual_pos = transform.to_virtual(event.pos)
            # Update event with virtual position for processing
            # (This is a simplified version - actual implementation would be more complex)

        return self._handle_event(event, transform)

    @abstractmethod
    def _handle_event(self, event: pygame.event.Event, transform: Transform) -> bool:
        """
        Override to handle specific events.

        Args:
            event: Pygame event
            transform: Transform for coordinate conversion

        Returns:
            True if event was consumed
        """
        return False

    def update(self, dt: float) -> None:
        """
        Update component state.

        Args:
            dt: Delta time in seconds
        """
        pass

    @abstractmethod
    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        """
        Render component.

        Args:
            surface: Surface to render to
            transform: Transform for coordinate conversion
        """
        pass

    def get_absolute_position(self) -> tuple[int, int]:
        """
        Get absolute position including parent offset.

        Returns:
            Absolute (x, y) coordinates
        """
        x, y = self.rect.topleft
        if self.parent:
            px, py = self.parent.get_absolute_position()
            x += px
            y += py
        return (x, y)


# Import at end to avoid circular imports
if TYPE_CHECKING:
    from .container import UIContainer
