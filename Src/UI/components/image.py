"""
Image component for displaying images.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

from UI.core.component import UIComponent

if TYPE_CHECKING:
    from UI.core.transform import Transform


class UIImage(UIComponent):
    """
    Image display component.

    Displays a pygame Surface image.
    """

    def __init__(self, image: pygame.Surface, **kwargs):
        """
        Initialize image component.

        Args:
            image: Pygame surface to display
            **kwargs: Additional arguments for UIComponent
        """
        # Get size from image if not provided
        if "size" not in kwargs:
            kwargs["size"] = (image.get_width(), image.get_height())

        super().__init__(**kwargs)

        self._image = image
        self._scaled_image: pygame.Surface | None = None

    def _handle_event(self, event: pygame.event.Event, transform: Transform) -> bool:
        """Images don't handle events."""
        return False

    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        """
        Render the image.

        Args:
            surface: Surface to render to
            transform: Transform for coordinate conversion
        """
        if not self.visible:
            return

        # Get absolute position
        abs_x, abs_y = self.get_absolute_position()
        abs_rect = pygame.Rect(abs_x, abs_y, self._size[0], self._size[1])
        screen_rect = transform.to_screen(abs_rect)

        # Scale image if needed
        if self._scaled_image is None or self._scaled_image.get_size() != (
            screen_rect.width,
            screen_rect.height,
        ):
            self._scaled_image = pygame.transform.scale(
                self._image, (screen_rect.width, screen_rect.height)
            )

        # Draw image
        surface.blit(self._scaled_image, screen_rect.topleft)
