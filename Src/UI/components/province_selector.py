"""Reusable province selector built on top of the province map widget."""

from __future__ import annotations

import math
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from UI.components.province_map import UIProvinceMap
from UI.core.gamepad_handler import GamepadButton
from UI.core.manager import UIManager

if TYPE_CHECKING:
    from UI.core.transform import Transform


class UIProvinceSelector(UIProvinceMap):
    """Province map with hover, selection, confirm, and cursor navigation."""

    NAV_MODE_ADJACENCY = "adjacency"
    NAV_MODE_CURSOR = "cursor"

    def __init__(
        self,
        on_province_changed: Callable[[int | None], None] | None = None,
        on_province_confirmed: Callable[[int], None] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.on_province_changed = on_province_changed
        self.on_province_confirmed = on_province_confirmed

        self._selected_province: int | None = None
        self._province_cycle_index = 0
        self._playable_province_order = self.playable_provinces or sorted(
            self.map_renderer.shape_manager.shapes.keys()
        )

        self._nav_mode = self.NAV_MODE_ADJACENCY
        self._cursor_visible = False
        self._cursor_pos = (0, 0)
        self._free_cursor_pos = (640.0, 400.0)
        self._free_cursor_speed = 12.0

        self._key_states: dict[int, bool] = {}
        self._key_repeat_delay = 0.15
        self._key_repeat_interval = 0.05
        self._key_press_times: dict[int, float] = {}
        self._key_last_repeat: dict[int, float] = {}

    def handle_gamepad_button(self, button: GamepadButton, transform: Transform) -> bool:
        """Handle gamepad input routed from the current screen."""
        if button in (GamepadButton.DPAD_UP, GamepadButton.LEFT_STICK_UP):
            return self._handle_direction("up", transform)
        if button in (GamepadButton.DPAD_DOWN, GamepadButton.LEFT_STICK_DOWN):
            return self._handle_direction("down", transform)
        if button in (GamepadButton.DPAD_LEFT, GamepadButton.LEFT_STICK_LEFT):
            return self._handle_direction("left", transform)
        if button in (GamepadButton.DPAD_RIGHT, GamepadButton.LEFT_STICK_RIGHT):
            return self._handle_direction("right", transform)
        if button == GamepadButton.A:
            return self._confirm_selected_province()
        if button == GamepadButton.SELECT:
            self.toggle_nav_mode(transform)
            return True
        return False

    def _handle_event(self, event: pygame.event.Event, transform: Transform) -> bool:
        """Handle mouse and keyboard events for province selection."""
        if event.type == pygame.MOUSEMOTION:
            province_id = self.get_province_at_screen_point(event.pos, transform)
            self._set_selected_province(province_id, transform)
            return province_id is not None

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            province_id = self.get_province_at_screen_point(event.pos, transform)
            self._set_selected_province(province_id, transform)
            return province_id is not None

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            province_id = self.get_province_at_screen_point(event.pos, transform)
            if province_id is not None:
                self._set_selected_province(province_id, transform)
                return self._confirm_selected_province()
            return False

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_TAB, pygame.K_s):
                self.toggle_nav_mode(transform)
                return True
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self._confirm_selected_province()
            if event.key == pygame.K_UP:
                self._track_repeat_key(event.key)
                return self._handle_direction("up", transform)
            if event.key == pygame.K_DOWN:
                self._track_repeat_key(event.key)
                return self._handle_direction("down", transform)
            if event.key == pygame.K_LEFT:
                self._track_repeat_key(event.key)
                return self._handle_direction("left", transform)
            if event.key == pygame.K_RIGHT:
                self._track_repeat_key(event.key)
                return self._handle_direction("right", transform)

        if event.type == pygame.KEYUP and event.key in self._key_states:
            self._clear_repeat_key(event.key)

        return False

    def update(self, dt: float) -> None:
        """Update animations and held-key cursor movement."""
        super().update(dt)

        if self._nav_mode != self.NAV_MODE_CURSOR or not self._key_states:
            return

        current_time = time.time()
        for key in list(self._key_states):
            if key not in self._key_press_times or self._key_press_times[key] == 0:
                self._key_press_times[key] = current_time
                self._key_last_repeat[key] = current_time
                continue

            elapsed = current_time - self._key_press_times[key]
            since_last = current_time - self._key_last_repeat[key]
            if elapsed <= self._key_repeat_delay or since_last <= self._key_repeat_interval:
                continue

            if key == pygame.K_UP:
                self._move_free_cursor(
                    0, -self._free_cursor_speed, UIManager.get_instance().transform
                )
            elif key == pygame.K_DOWN:
                self._move_free_cursor(
                    0, self._free_cursor_speed, UIManager.get_instance().transform
                )
            elif key == pygame.K_LEFT:
                self._move_free_cursor(
                    -self._free_cursor_speed, 0, UIManager.get_instance().transform
                )
            elif key == pygame.K_RIGHT:
                self._move_free_cursor(
                    self._free_cursor_speed, 0, UIManager.get_instance().transform
                )

            self._key_last_repeat[key] = current_time

    def get_selected_province(self) -> int | None:
        """Return the currently selected province."""
        return self._selected_province

    def set_selected_province(
        self, province_id: int | None, transform: Transform | None = None
    ) -> None:
        """Public setter for the currently selected province."""
        self._set_selected_province(province_id, transform)

    def toggle_nav_mode(self, transform: Transform | None = None) -> None:
        """Toggle between adjacency and free-cursor navigation."""
        if self._nav_mode == self.NAV_MODE_ADJACENCY:
            self._nav_mode = self.NAV_MODE_CURSOR
            if self._selected_province and transform:
                cursor_pos = self.get_province_screen_position(
                    self._selected_province, transform, anchor="number"
                )
                if cursor_pos:
                    self._free_cursor_pos = (float(cursor_pos[0]), float(cursor_pos[1]))
                    self._cursor_pos = cursor_pos
                    self._cursor_visible = True
        else:
            self._nav_mode = self.NAV_MODE_ADJACENCY
            if transform:
                self._select_province_at_cursor(transform)

    def _handle_direction(self, direction: str, transform: Transform) -> bool:
        if self._nav_mode == self.NAV_MODE_CURSOR:
            delta = self._free_cursor_speed
            if direction == "up":
                self._move_free_cursor(0, -delta, transform)
            elif direction == "down":
                self._move_free_cursor(0, delta, transform)
            elif direction == "left":
                self._move_free_cursor(-delta, 0, transform)
            else:
                self._move_free_cursor(delta, 0, transform)
            return True

        self._navigate_by_direction(direction, transform)
        return True

    def _track_repeat_key(self, key: int) -> None:
        self._key_states[key] = True
        self._key_press_times[key] = 0
        self._key_last_repeat[key] = 0

    def _clear_repeat_key(self, key: int) -> None:
        del self._key_states[key]
        self._key_press_times.pop(key, None)
        self._key_last_repeat.pop(key, None)

    def _set_selected_province(self, province_id: int | None, transform: Transform | None) -> None:
        province_id = province_id if self._is_playable(province_id) else None
        if province_id == self._selected_province:
            self.set_hovered_province(province_id)
            return

        self._selected_province = province_id
        self.set_hovered_province(province_id)
        self.set_highlighted_provinces([province_id] if province_id else [])

        if province_id in self._playable_province_order:
            self._province_cycle_index = self._playable_province_order.index(province_id)

        if province_id and transform:
            cursor_pos = self.get_province_screen_position(province_id, transform, anchor="number")
            if cursor_pos:
                self._cursor_pos = cursor_pos
                self._free_cursor_pos = (float(cursor_pos[0]), float(cursor_pos[1]))
                self._cursor_visible = True
        elif province_id is None:
            self._cursor_visible = False

        if self.on_province_changed:
            self.on_province_changed(province_id)

    def _navigate_by_direction(self, direction: str, transform: Transform) -> None:
        if not self._selected_province:
            if self._playable_province_order:
                self._set_selected_province(self._playable_province_order[0], transform)
            return

        current_shape = self.map_renderer.shape_manager.get_shape(self._selected_province)
        if not current_shape:
            self._navigate_by_index(-1 if direction in ("up", "left") else 1, transform)
            return

        current_x, current_y = current_shape.number_position
        neighbors = [
            neighbor_id
            for neighbor_id in self.map_renderer.shape_manager.get_neighbors(
                self._selected_province
            )
            if self._is_playable(neighbor_id)
        ]
        if not neighbors:
            self._navigate_by_index(-1 if direction in ("up", "left") else 1, transform)
            return

        best_neighbor = None
        best_score: tuple[float, float] | None = None
        direction_vectors = {
            "up": (0.0, -1.0),
            "down": (0.0, 1.0),
            "left": (-1.0, 0.0),
            "right": (1.0, 0.0),
        }
        target_dx, target_dy = direction_vectors[direction]

        for neighbor_id in neighbors:
            shape = self.map_renderer.shape_manager.get_shape(neighbor_id)
            if not shape:
                continue

            dx = shape.number_position[0] - current_x
            dy = shape.number_position[1] - current_y
            distance = math.hypot(dx, dy)
            if distance == 0:
                continue

            normalized_dx = dx / distance
            normalized_dy = dy / distance
            alignment = normalized_dx * target_dx + normalized_dy * target_dy
            if alignment <= 0:
                continue

            score = (-alignment, distance)
            if best_score is None or score < best_score:
                best_score = score
                best_neighbor = neighbor_id

        if best_neighbor is not None:
            self._set_selected_province(best_neighbor, transform)
        else:
            self._navigate_by_index(-1 if direction in ("up", "left") else 1, transform)

    def _navigate_by_index(self, delta: int, transform: Transform) -> None:
        if not self._playable_province_order:
            return
        self._province_cycle_index = (self._province_cycle_index + delta) % len(
            self._playable_province_order
        )
        self._set_selected_province(
            self._playable_province_order[self._province_cycle_index], transform
        )

    def _move_free_cursor(self, dx: float, dy: float, transform: Transform) -> None:
        bounds = self._get_screen_rect(transform)
        x = max(bounds.left, min(bounds.right, self._free_cursor_pos[0] + dx))
        y = max(bounds.top, min(bounds.bottom, self._free_cursor_pos[1] + dy))
        self._free_cursor_pos = (x, y)
        self._cursor_pos = (int(x), int(y))
        self._cursor_visible = True
        self._select_province_at_cursor(transform)

    def _select_province_at_cursor(self, transform: Transform) -> None:
        province_id = self.get_province_at_screen_point(
            (int(self._free_cursor_pos[0]), int(self._free_cursor_pos[1])), transform
        )
        if province_id is not None:
            self._set_selected_province(province_id, transform)

    def _confirm_selected_province(self) -> bool:
        if self._selected_province is None or not self.on_province_confirmed:
            return False
        self.on_province_confirmed(self._selected_province)
        return True

    def render(self, surface: pygame.Surface, transform: Transform) -> None:
        super().render(surface, transform)
        if self._cursor_visible and self._selected_province is not None:
            self._draw_cursor(surface, self._cursor_pos)

    def _draw_cursor(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        t = time.time()
        pulse = abs(math.sin(t * 4))
        size = 30 + int(pulse * 8)

        x, y = pos
        yellow = (255, 255, 100)
        orange = (255, 180, 50)

        glow_radius = size + 10
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        alpha = int(100 + pulse * 100)
        pygame.draw.circle(
            glow_surface, (255, 255, 100, alpha), (glow_radius, glow_radius), glow_radius
        )
        surface.blit(glow_surface, (x - glow_radius, y - glow_radius))

        pygame.draw.line(surface, yellow, (x - size, y), (x + size, y), 4)
        pygame.draw.line(surface, yellow, (x, y - size), (x, y + size), 4)

        corner_size = size // 2
        bracket_width = 4
        pygame.draw.line(
            surface, orange, (x - size, y - size), (x - size + corner_size, y - size), bracket_width
        )
        pygame.draw.line(
            surface, orange, (x - size, y - size), (x - size, y - size + corner_size), bracket_width
        )
        pygame.draw.line(
            surface, orange, (x + size, y - size), (x + size - corner_size, y - size), bracket_width
        )
        pygame.draw.line(
            surface, orange, (x + size, y - size), (x + size, y - size + corner_size), bracket_width
        )
        pygame.draw.line(
            surface, orange, (x - size, y + size), (x - size + corner_size, y + size), bracket_width
        )
        pygame.draw.line(
            surface, orange, (x - size, y + size), (x - size, y + size - corner_size), bracket_width
        )
        pygame.draw.line(
            surface, orange, (x + size, y + size), (x + size - corner_size, y + size), bracket_width
        )
        pygame.draw.line(
            surface, orange, (x + size, y + size), (x + size, y + size - corner_size), bracket_width
        )

        center_size = int(6 + pulse * 3)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), center_size)
        pygame.draw.circle(surface, yellow, (x, y), center_size - 2)
