"""
UI Container class.

Containers hold and manage child components.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from .component import UIComponent

if TYPE_CHECKING:
    from .anchor import Anchor, Position
    from .transform import Transform


class UIContainer(UIComponent):
    """
        Container for grouping and laying out child components.

        Containers can have backgrounds, borders, padding, and manage
    the layout of their children.

        Attributes:
            children: List of child components
            background_color: Background fill color
            border_color: Border color
            border_width: Border thickness
            padding: Space inside the border
    """

    def __init__(
        self,
        position: tuple[int | float | str, int | float | str] | Position = (0, 0),
        size: tuple[int, int] | None = None,
        anchor: Anchor | None = None,
        parent: UIContainer | None = None,
        background_color: pygame.Color | tuple[int, int, int] | None = None,
        border_color: pygame.Color | tuple[int, int, int] | None = None,
        border_width: int = 0,
        padding: int | tuple[int, int] | tuple[int, int, int, int] = 0,
    ):
        """
        Initialize container.

        Args:
            position: Position as (x, y) tuple or Position object
            size: Size as (width, height) tuple
            anchor: Positioning anchor
            parent: Parent container
            background_color: Background color or None for transparent
            border_color: Border color
            border_width: Border thickness in pixels
            padding: Padding as single int, (x, y) tuple, or (top, right, bottom, left) tuple
        """
        super().__init__(position, size, anchor, parent)

        self.children: list[UIComponent] = []
        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width

        # Normalize padding to (top, right, bottom, left)
        if isinstance(padding, int):
            self.padding = (padding, padding, padding, padding)
        elif len(padding) == 2:
            self.padding = (padding[0], padding[1], padding[0], padding[1])
        else:
            self.padding = padding

    def add_child(self, child: UIComponent) -> None:
        """
        Add a child component.

        Args:
            child: Component to add
        """
        if child not in self.children:
            self.children.append(child)
            child.parent = self

    def remove_child(self, child: UIComponent) -> None:
        """
        Remove a child component.

        Args:
            child: Component to remove
        """
        if child in self.children:
            self.children.remove(child)
            child.parent = None

    def get_children(self) -> list[UIComponent]:
        """
        Get all child components.

        Returns:
            List of child components
        """
        return self.children.copy()

    def clear_children(self) -> None:
        """Remove all child components."""
        for child in self.children:
            child.parent = None
        self.children.clear()

    def get_content_rect(self) -> pygame.Rect:
        """
        Get rectangle available for children (accounting for padding).

        Returns:
            Content rectangle in virtual coordinates
        """
        r = self.rect
        return pygame.Rect(
            r.x + self.padding[3],  # left
            r.y + self.padding[0],  # top
            r.width - self.padding[3] - self.padding[1],  # width - left - right
            r.height - self.padding[0] - self.padding[2],  # height - top - bottom
        )

    def find_component_at(self, point: tuple[int, int], transform: Transform) -> UIComponent | None:
        """
        Find the topmost component at a screen point.

        Searches children in reverse order (newest first).

        Args:
            point: Screen coordinates (x, y)
            transform: Transform for coordinate conversion

        Returns:
            Component at point, or None
        """
        if not self.visible:
            return None

        # Check children first (in reverse order for topmost)
        for child in reversed(self.children):
            if isinstance(child, UIContainer):
                result = child.find_component_at(point, transform)
                if result:
                    return result
            elif child.contains_point(point, transform):
                return child

        # Check self
        if self.contains_point(point, transform):
            return self

        return None

    def _handle_event(self, event: pygame.event.Event, transform: Transform) -> bool:
        """
        Pass event to children.

        Args:
            event: Pygame event
            transform: Transform for coordinate conversion

        Returns:
            True if any child consumed the event
        """
        # Pass to children in reverse order (topmost first)
        for child in reversed(self.children):
            if child.handle_event(event, transform):
                return True
        return False

    def update(self, dt: float) -> None:
        """
        Update container and children.

        Args:
            dt: Delta time in seconds
        """
        super().update(dt)

        for child in self.children:
            if child.visible:
                child.update(dt)

    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        """
        Render container and children.

        Args:
            surface: Surface to render to
            transform: Transform for coordinate conversion
        """
        if not self.visible:
            return

        # Get absolute position for rendering
        abs_x, abs_y = self.get_absolute_position()
        abs_rect = pygame.Rect(abs_x, abs_y, self._size[0], self._size[1])
        screen_rect = transform.to_screen(abs_rect)

        # Draw background
        if self.background_color:
            pygame.draw.rect(surface, self.background_color, screen_rect)

        # Draw border
        if self.border_width > 0 and self.border_color:
            pygame.draw.rect(surface, self.border_color, screen_rect, self.border_width)

        # Render children
        for child in self.children:
            child.render(surface, transform)

    def layout_children(self) -> None:
        """
        Apply layout to children.

        Override in subclasses to implement specific layout algorithms.
        """
        pass


# Import at end to avoid circular imports
if TYPE_CHECKING:
    from .anchor import Anchor, Position
