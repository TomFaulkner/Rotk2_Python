"""
Transform and resolution scaling system.

Handles conversion between virtual coordinates (design resolution)
and actual screen coordinates.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    pass


class Transform:
    """
    Handles scaling from virtual to actual resolution.

    Design at 1280x800, scale to any resolution while maintaining
    aspect ratio (letterboxing if needed).

    Attributes:
        virtual_size: The design resolution (e.g., 1280x800)
        actual_size: The actual screen resolution
        scale: Uniform scale factor (maintains aspect ratio)
        offset_x: Horizontal letterbox offset
        offset_y: Vertical letterbox offset
    """

    def __init__(
        self,
        virtual_size: tuple[int, int],
        actual_size: tuple[int, int],
        maintain_aspect: bool = True,
    ):
        """
        Initialize transform.

        Args:
            virtual_size: Design resolution (width, height)
            actual_size: Actual screen resolution (width, height)
            maintain_aspect: If True, maintain aspect ratio with letterboxing
        """
        self.virtual_size = virtual_size
        self.actual_size = actual_size
        self.maintain_aspect = maintain_aspect

        if maintain_aspect:
            # Calculate uniform scale to fit virtual within actual
            self.scale = min(actual_size[0] / virtual_size[0], actual_size[1] / virtual_size[1])
            # Center the scaled content
            self.offset_x = (actual_size[0] - virtual_size[0] * self.scale) / 2
            self.offset_y = (actual_size[1] - virtual_size[1] * self.scale) / 2
            self.scale_x = self.scale
            self.scale_y = self.scale
        else:
            # Stretch to fill (may distort aspect ratio)
            self.scale_x = actual_size[0] / virtual_size[0]
            self.scale_y = actual_size[1] / virtual_size[1]
            self.scale = (self.scale_x + self.scale_y) / 2
            self.offset_x = 0
            self.offset_y = 0

    def to_screen(self, rect: pygame.Rect) -> pygame.Rect:
        """
        Convert virtual rectangle to screen coordinates.

        Args:
            rect: Rectangle in virtual coordinates

        Returns:
            Rectangle in screen coordinates
        """
        return pygame.Rect(
            int(rect.x * self.scale_x + self.offset_x),
            int(rect.y * self.scale_y + self.offset_y),
            int(rect.width * self.scale_x),
            int(rect.height * self.scale_y),
        )

    def to_virtual(self, point: tuple[int, int]) -> tuple[float, float]:
        """
        Convert screen point to virtual coordinates.

        Args:
            point: Screen coordinates (x, y)

        Returns:
            Virtual coordinates (x, y)
        """
        x, y = point
        return ((x - self.offset_x) / self.scale_x, (y - self.offset_y) / self.scale_y)

    def scale_distance(self, distance: int) -> int:
        """
        Scale a distance (e.g., font size, border width).

        Uses uniform scale to maintain proportions.

        Args:
            distance: Distance in virtual pixels

        Returns:
            Distance in screen pixels
        """
        return int(distance * self.scale)

    def get_scale(self) -> float:
        """Get uniform scale factor."""
        return self.scale

    def get_scale_tuple(self) -> tuple[float, float]:
        """Get (scale_x, scale_y) tuple."""
        return (self.scale_x, self.scale_y)

    def get_letterbox_rect(self) -> pygame.Rect:
        """
        Get the rectangle representing the letterboxed area.

        Returns:
            Rectangle in screen coordinates of the playable area
        """
        width = self.virtual_size[0] * self.scale
        height = self.virtual_size[1] * self.scale
        return pygame.Rect(int(self.offset_x), int(self.offset_y), int(width), int(height))

    def is_inside_letterbox(self, point: tuple[int, int]) -> bool:
        """
        Check if a screen point is inside the letterboxed area.

        Args:
            point: Screen coordinates (x, y)

        Returns:
            True if point is inside the playable area
        """
        letterbox = self.get_letterbox_rect()
        return letterbox.collidepoint(point)
