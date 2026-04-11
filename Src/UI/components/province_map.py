"""Reusable province map view with overlay support."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import pygame

from UI.core.component import UIComponent
from UI.map.map_renderer import MapRenderer

if TYPE_CHECKING:
    from UI.core.transform import Transform


@dataclass
class ProvinceMapAnimation:
    """Base interface for custom map animations."""

    def update(self, dt: float) -> None:
        """Advance animation state."""

    def render(
        self,
        surface: pygame.Surface,
        province_map: UIProvinceMap,
        transform: Transform,
    ) -> None:
        """Render the animation on top of the map."""


class UIProvinceMap(UIComponent):
    """Reusable world map widget with hit testing and overlays."""

    DEFAULT_BG_COLOR = (40, 40, 60)
    DEFAULT_BORDER_COLOR = (79, 189, 186)
    DEFAULT_HIGHLIGHT_COLOR = (255, 255, 200)
    DEFAULT_ICON_TEXT_COLOR = (255, 255, 255)
    DEFAULT_ICON_BG_COLOR = (160, 40, 40)

    def __init__(
        self,
        playable_provinces: list[int] | None = None,
        show_numbers: bool = True,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.map_renderer = MapRenderer()
        self.map_renderer.set_show_numbers(show_numbers)

        bg_path = Path(__file__).parent.parent.parent.parent / "download" / "numbers-removed.jpg"
        self.map_renderer.load_terrain_background(str(bg_path))

        self.playable_provinces = playable_provinces
        self.hovered_province: int | None = None
        self.highlighted_provinces: set[int] = set()
        self.province_icons: dict[int, pygame.Surface] = {}
        self.animations: list[ProvinceMapAnimation] = []

        self.background_color = self.DEFAULT_BG_COLOR
        self.border_color = self.DEFAULT_BORDER_COLOR
        self.border_width = 2

    def _handle_event(self, event: pygame.event.Event, transform: Transform) -> bool:
        """Base map does not consume input by itself."""
        return False

    def update(self, dt: float) -> None:
        """Update active animations."""
        for animation in self.animations:
            animation.update(dt)

    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        """Render the map, highlights, icons, and animations."""
        if not self.visible:
            return

        rect = self._get_screen_rect(transform)
        pygame.draw.rect(surface, self.background_color, rect)
        pygame.draw.rect(surface, self.border_color, rect, self.border_width)

        self.map_renderer.render(surface, transform, screen_offset=rect.topleft)

        for province_id in self.highlighted_provinces:
            self.map_renderer.render_province_highlight(
                surface, province_id, transform, screen_offset=rect.topleft
            )

        self._render_icons(surface, transform)

        for animation in self.animations:
            animation.render(surface, self, transform)

    def _get_screen_rect(self, transform: Transform) -> pygame.Rect:
        abs_x, abs_y = self.get_absolute_position()
        abs_rect = pygame.Rect(abs_x, abs_y, self._size[0], self._size[1])
        return transform.to_screen(abs_rect)

    def _is_playable(self, province_id: int | None) -> bool:
        if province_id is None:
            return False
        if self.playable_provinces is None:
            return True
        return province_id in self.playable_provinces

    def get_province_at_screen_point(
        self, screen_point: tuple[int, int], transform: Transform
    ) -> int | None:
        """Resolve a screen point to a playable province."""
        province_id = self.map_renderer.get_province_at_screen_point(
            screen_point,
            transform,
            screen_offset=self._get_screen_rect(transform).topleft,
        )
        if self._is_playable(province_id):
            return province_id
        return None

    def get_province_screen_position(
        self, province_id: int, transform: Transform, anchor: str = "number"
    ) -> tuple[int, int] | None:
        """Get a province anchor point in screen coordinates."""
        if not self._is_playable(province_id):
            return None
        return self.map_renderer.get_province_screen_position(
            province_id,
            transform,
            anchor=anchor,
            screen_offset=self._get_screen_rect(transform).topleft,
        )

    def set_hovered_province(self, province_id: int | None) -> None:
        """Track the province under the mouse or cursor."""
        self.hovered_province = province_id if self._is_playable(province_id) else None

    def set_highlighted_provinces(
        self, province_ids: set[int] | list[int] | tuple[int, ...]
    ) -> None:
        """Replace the highlighted province set."""
        self.highlighted_provinces = {
            province_id for province_id in province_ids if self._is_playable(province_id)
        }

    def clear_highlights(self) -> None:
        """Remove all province highlights."""
        self.highlighted_provinces.clear()

    def set_province_icon(self, province_id: int, icon: pygame.Surface) -> None:
        """Set an overlay icon for a province."""
        if self._is_playable(province_id):
            self.province_icons[province_id] = icon

    def set_province_text_icon(
        self,
        province_id: int,
        text: str,
        font: pygame.font.Font | None = None,
        text_color: tuple[int, int, int] = DEFAULT_ICON_TEXT_COLOR,
        background_color: tuple[int, int, int] = DEFAULT_ICON_BG_COLOR,
        padding: int = 4,
    ) -> None:
        """Create a simple text badge icon for a province."""
        font = font or pygame.font.Font(None, 22)
        label = font.render(text, True, text_color)
        icon = pygame.Surface(
            (label.get_width() + padding * 2, label.get_height() + padding * 2), pygame.SRCALPHA
        )
        pygame.draw.rect(icon, background_color, icon.get_rect(), border_radius=4)
        icon.blit(label, (padding, padding))
        self.set_province_icon(province_id, icon)

    def clear_province_icon(self, province_id: int) -> None:
        """Remove an overlay icon from a province."""
        self.province_icons.pop(province_id, None)

    def clear_province_icons(self) -> None:
        """Remove all overlay icons."""
        self.province_icons.clear()

    def add_animation(self, animation: ProvinceMapAnimation) -> None:
        """Register a custom animation overlay."""
        self.animations.append(animation)

    def clear_animations(self) -> None:
        """Remove all custom animations."""
        self.animations.clear()

    def _render_icons(self, surface: pygame.Surface, transform: Transform) -> None:
        for province_id, icon in self.province_icons.items():
            icon_pos = self.get_province_screen_position(province_id, transform, anchor="number")
            if not icon_pos:
                continue
            icon_rect = icon.get_rect(midbottom=(icon_pos[0], icon_pos[1] - 14))
            surface.blit(icon, icon_rect)
