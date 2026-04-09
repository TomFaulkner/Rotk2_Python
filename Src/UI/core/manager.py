"""
UI Manager singleton.

Central coordinator for the UI system.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from .anchor import UIMode
from .transform import Transform
from .container import UIContainer

if TYPE_CHECKING:
    from .component import UIComponent


class UIManager:
    """
    Central UI manager singleton.

    Manages the current screen, handles input events, coordinates rendering,
    and manages resolution scaling.

    Attributes:
        virtual_resolution: Design resolution (default 1280x800)
        actual_resolution: Current screen resolution
        mode: UI mode (CLASSIC or MODERN)
        current_screen: Active screen component
        focused_component: Currently focused component (for keyboard/gamepad)
        transform: Transform for coordinate conversion
    """

    _instance: UIManager | None = None

    def __new__(cls, *args, **kwargs) -> UIManager:
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(
        self, virtual_resolution: tuple[int, int] = (1280, 800), mode: UIMode = UIMode.MODERN
    ):
        """
        Initialize UI manager.

        Args:
            virtual_resolution: Design resolution (width, height)
            mode: UI mode (CLASSIC or MODERN)
        """
        # Avoid re-initialization
        if self._initialized:
            return

        self.virtual_resolution = virtual_resolution
        self.actual_resolution = virtual_resolution
        self.mode = mode
        self._initialized = True

        # Screen management
        self.current_screen: UIContainer | None = None
        self.modal_dialog: UIContainer | None = None

        # Focus management
        self.focused_component: UIComponent | None = None
        self.hover_component: UIComponent | None = None

        # Transform for coordinate conversion
        self.transform = Transform(self.virtual_resolution, self.actual_resolution)

        # Debug
        self.debug_mode = False

    @classmethod
    def get_instance(cls) -> UIManager:
        """Get the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (for testing)."""
        cls._instance = None

    def set_screen(self, screen: UIContainer) -> None:
        """
        Set the current active screen.

        Args:
            screen: Screen to activate
        """
        self.current_screen = screen
        self.focused_component = None
        self.hover_component = None

    def set_resolution(self, width: int, height: int, maintain_aspect: bool = True) -> None:
        """
        Change the actual screen resolution.

        Args:
            width: New screen width
            height: New screen height
            maintain_aspect: If True, maintain aspect ratio with letterboxing
        """
        self.actual_resolution = (width, height)
        self.transform = Transform(self.virtual_resolution, self.actual_resolution, maintain_aspect)

    def set_mode(self, mode: UIMode) -> None:
        """
        Set UI mode.

        Args:
            mode: UI mode (CLASSIC or MODERN)
        """
        self.mode = mode
        if mode == UIMode.CLASSIC:
            self.virtual_resolution = (640, 400)
        else:
            self.virtual_resolution = (1280, 800)

        # Recreate transform
        self.transform = Transform(self.virtual_resolution, self.actual_resolution)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle a pygame event.

        Args:
            event: Pygame event to handle

        Returns:
            True if event was consumed
        """
        if not self.current_screen:
            return False

        # Handle window resize
        if event.type == pygame.VIDEORESIZE:
            self.set_resolution(event.w, event.h)
            return True

        # Handle mouse motion for hover
        if event.type == pygame.MOUSEMOTION:
            component = self._find_component_at(event.pos)
            if component != self.hover_component:
                # Mouse left previous component
                if self.hover_component and hasattr(self.hover_component, "on_mouse_leave"):
                    self.hover_component.on_mouse_leave()
                # Mouse entered new component
                if component and hasattr(component, "on_mouse_enter"):
                    component.on_mouse_enter()
                self.hover_component = component

        # Pass event to current screen
        return self.current_screen.handle_event(event, self.transform)

    def _find_component_at(self, point: tuple[int, int]) -> UIComponent | None:
        """
        Find component at screen point.

        Args:
            point: Screen coordinates (x, y)

        Returns:
            Component at point, or None
        """
        if not self.current_screen:
            return None

        if isinstance(self.current_screen, UIContainer):
            return self.current_screen.find_component_at(point, self.transform)
        elif self.current_screen.contains_point(point, self.transform):
            return self.current_screen
        return None

    def set_focus(self, component: UIComponent | None) -> None:
        """
        Set the focused component.

        Args:
            component: Component to focus, or None to clear focus
        """
        if self.focused_component:
            self.focused_component.set_focus(False)

        self.focused_component = component

        if component:
            component.set_focus(True)

    def move_focus(self, direction: str) -> None:
        """
        Move focus in a direction (for keyboard/gamepad navigation).

        Args:
            direction: One of 'up', 'down', 'left', 'right', 'next', 'previous'
        """
        # TODO: Implement focus navigation
        pass

    def update(self, dt: float) -> None:
        """
        Update all UI components.

        Args:
            dt: Delta time in seconds
        """
        if self.current_screen:
            self.current_screen.update(dt)

    def render(self, surface: pygame.Surface) -> None:
        """
        Render the UI.

        Args:
            surface: Surface to render to
        """
        # Clear letterbox area if needed
        if self.transform.maintain_aspect:
            letterbox = self.transform.get_letterbox_rect()
            # Fill outside letterbox with black
            full_rect = surface.get_rect()
            # Top bar
            if letterbox.top > 0:
                pygame.draw.rect(surface, (0, 0, 0), (0, 0, full_rect.width, letterbox.top))
            # Bottom bar
            if letterbox.bottom < full_rect.height:
                pygame.draw.rect(
                    surface,
                    (0, 0, 0),
                    (0, letterbox.bottom, full_rect.width, full_rect.height - letterbox.bottom),
                )
            # Left bar
            if letterbox.left > 0:
                pygame.draw.rect(surface, (0, 0, 0), (0, 0, letterbox.left, full_rect.height))
            # Right bar
            if letterbox.right < full_rect.width:
                pygame.draw.rect(
                    surface,
                    (0, 0, 0),
                    (letterbox.right, 0, full_rect.width - letterbox.right, full_rect.height),
                )

        # Render current screen
        if self.current_screen:
            self.current_screen.render(surface, self.transform)

        # Render debug info if enabled
        if self.debug_mode:
            self._render_debug(surface)

    def _render_debug(self, surface: pygame.Surface) -> None:
        """Render debug overlay."""
        # TODO: Implement debug overlay (FPS, component count, etc.)
        pass

    def get_virtual_mouse_pos(self) -> tuple[float, float]:
        """
        Get mouse position in virtual coordinates.

        Returns:
            Mouse position (x, y) in virtual coordinates
        """
        mouse_pos = pygame.mouse.get_pos()
        return self.transform.to_virtual(mouse_pos)
