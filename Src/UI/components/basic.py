"""
Basic UI components.

Label, Button, Panel, and other fundamental components.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

import pygame

from UI.core.component import UIComponent
from UI.core.container import UIContainer
from UI.core.anchor import Anchor
from UI.core.transform import Transform

if TYPE_CHECKING:
    from UI.core.anchor import Position


class UILabel(UIComponent):
    """
    Text label component.

    Displays text with optional word wrap and alignment.

    Attributes:
        text: The text to display
        font: Pygame font to use
        color: Text color
        align: Text alignment
    """

    def __init__(
        self,
        text: str = "",
        font: pygame.font.Font | None = None,
        color: pygame.Color | tuple[int, int, int] = (255, 255, 255),
        align: str = "left",
        **kwargs,
    ):
        """
        Initialize label.

        Args:
            text: Text to display
            font: Pygame font, or None for default
            color: Text color
            align: Text alignment ('left', 'center', 'right')
            **kwargs: Additional arguments for UIComponent
        """
        super().__init__(**kwargs)

        self._text = text
        self.font = font or pygame.font.Font(None, 24)
        self.color = color
        self.align = align

        # Cached rendered surface
        self._rendered: pygame.Surface | None = None
        self._needs_render = True

    @property
    def text(self) -> str:
        """Get current text."""
        return self._text

    @text.setter
    def text(self, value: str) -> None:
        """Set text and mark for re-render."""
        if value != self._text:
            self._text = value
            self._needs_render = True

    def get_preferred_size(self) -> tuple[int, int]:
        """
        Calculate preferred size based on text.

        Returns:
            (width, height) tuple
        """
        lines = self._text.split("\n")
        max_width = 0
        total_height = 0

        for line in lines:
            surface = self.font.render(line, True, self.color)
            max_width = max(max_width, surface.get_width())
            total_height += surface.get_height()

        return (max_width, total_height)

    def _handle_event(self, event: pygame.event.Event, transform: Transform) -> bool:
        """Labels don't handle events."""
        return False

    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        """
        Render label text.

        Args:
            surface: Surface to render to
            transform: Transform for coordinate conversion
        """
        if not self.visible:
            return

        # Re-render text if needed
        if self._needs_render or self._rendered is None:
            self._rendered = self.font.render(self._text, True, self.color)
            self._needs_render = False

        # Get absolute position
        abs_x, abs_y = self.get_absolute_position()
        abs_rect = pygame.Rect(abs_x, abs_y, self._size[0], self._size[1])
        screen_rect = transform.to_screen(abs_rect)

        # Calculate position based on alignment
        if self.align == "center":
            x = screen_rect.centerx - self._rendered.get_width() // 2
            y = screen_rect.centery - self._rendered.get_height() // 2
        elif self.align == "right":
            x = screen_rect.right - self._rendered.get_width()
            y = screen_rect.centery - self._rendered.get_height() // 2
        else:  # left
            x = screen_rect.left
            y = screen_rect.centery - self._rendered.get_height() // 2

        # Draw text
        surface.blit(self._rendered, (x, y))


class UIButton(UIContainer):
    """
    Button component.

    Clickable button with text and/or icon.

    States:
        - Normal: Default state
        - Hover: Mouse is over button
        - Pressed: Mouse button is held down
        - Focused: Has keyboard/gamepad focus
        - Disabled: Cannot be interacted with

    Attributes:
        text: Button text
        on_click: Callback when button is clicked
        shortcut_key: Keyboard shortcut key
    """

    def __init__(
        self,
        text: str = "",
        on_click: Callable[[], None] | None = None,
        shortcut_key: int | None = None,
        normal_color: pygame.Color | tuple[int, int, int] = (100, 100, 100),
        hover_color: pygame.Color | tuple[int, int, int] = (150, 150, 150),
        pressed_color: pygame.Color | tuple[int, int, int] = (80, 80, 80),
        text_color: pygame.Color | tuple[int, int, int] = (255, 255, 255),
        font: pygame.font.Font | None = None,
        **kwargs,
    ):
        """
        Initialize button.

        Args:
            text: Button text
            on_click: Callback function for click
            shortcut_key: Keyboard shortcut key code
            normal_color: Normal state background color
            hover_color: Hover state background color
            pressed_color: Pressed state background color
            text_color: Text color
            font: Font for text
            **kwargs: Additional arguments for UIContainer
        """
        super().__init__(**kwargs)

        self.text = text
        self.on_click = on_click
        self.shortcut_key = shortcut_key

        # Colors
        self.normal_color = normal_color
        self.hover_color = hover_color
        self.pressed_color = pressed_color
        self.text_color = text_color

        # Font
        self.font = font or pygame.font.Font(None, 24)

        # State
        self._hovered = False
        self._pressed = False

        # Create label child centered in button
        self.label = UILabel(
            text=text,
            font=self.font,
            color=text_color,
            align="center",
            position=(self._size[0] // 2, self._size[1] // 2),
            anchor=Anchor.CENTER,
            size=(self._size[0] - 10, self._size[1]),
        )
        self.add_child(self.label)

    def _handle_event(self, event: pygame.event.Event, transform: Transform) -> bool:
        """
        Handle button events.

        Args:
            event: Pygame event
            transform: Transform for coordinate conversion

        Returns:
            True if event was consumed
        """
        if not self.enabled:
            return False

        if event.type == pygame.MOUSEMOTION:
            # Hover state handled by UIManager
            pass

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                # Only press if mouse is actually over this button
                if self.contains_point(event.pos, transform):
                    self._pressed = True
                    return True

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self._pressed:
                self._pressed = False
                # Check if mouse is still over the button (not just _hovered state)
                if self.contains_point(event.pos, transform) and self.on_click:
                    self.on_click()
                return True

        elif event.type == pygame.KEYDOWN:
            if event.key == self.shortcut_key:
                if self.on_click:
                    self.on_click()
                return True
            # Space or Enter activates focused button
            if self.focused and event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self.on_click:
                    self.on_click()
                return True

        return False

    def on_mouse_enter(self) -> None:
        """Called when mouse enters button."""
        self._hovered = True

    def on_mouse_leave(self) -> None:
        """Called when mouse leaves button."""
        self._hovered = False
        self._pressed = False

    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        """
        Render button.

        Args:
            surface: Surface to render to
            transform: Transform for coordinate conversion
        """
        if not self.visible:
            return

        # Determine background color based on state
        if not self.enabled:
            bg_color = (50, 50, 50)
        elif self._pressed:
            bg_color = self.pressed_color
        elif self._hovered:
            bg_color = self.hover_color
        else:
            bg_color = self.normal_color

        # Get absolute position for rendering
        abs_x, abs_y = self.get_absolute_position()
        abs_rect = pygame.Rect(abs_x, abs_y, self._size[0], self._size[1])
        screen_rect = transform.to_screen(abs_rect)

        # Draw button background
        pygame.draw.rect(surface, bg_color, screen_rect)

        # Draw border if focused
        if self.focused:
            pygame.draw.rect(surface, (255, 255, 255), screen_rect, 2)

        # Render children (label)
        for child in self.children:
            child.render(surface, transform)


class UIPanel(UIContainer):
    """
    Simple panel container.

    A container with background color and optional border.
    Useful for grouping related UI elements.
    """

    def __init__(
        self,
        background_color: pygame.Color | tuple[int, int, int] | None = None,
        border_color: pygame.Color | tuple[int, int, int] | None = None,
        border_width: int = 0,
        **kwargs,
    ):
        """
        Initialize panel.

        Args:
            background_color: Background fill color, or None for transparent
            border_color: Border color
            border_width: Border thickness
            **kwargs: Additional arguments for UIContainer
        """
        super().__init__(**kwargs)

        self.background_color = background_color
        self.border_color = border_color
        self.border_width = border_width
