#!/usr/bin/env python3
# ruff: noqa: E402
"""Animate a dot traveling from province 1 to 35 and back."""

from __future__ import annotations

import sys
from pathlib import Path

root = Path(__file__).parent.parent
sys.path.insert(0, str(root))
sys.path.insert(0, str(root / "Src"))
sys.path.insert(0, str(root / "Src" / "UI"))
sys.path.insert(0, str(root / "Src" / "UI" / "core"))
sys.path.insert(0, str(root / "Src" / "UI" / "map"))

import pygame
from UI.components.province_map import ProvinceMapAnimation, UIProvinceMap
from UI.core.container import UIContainer
from UI.core.manager import UIManager
from UI.core.transform import Transform
from UI.map import ProvinceShapeManager, find_shortest_province_path


class ProvinceRouteDotAnimation(ProvinceMapAnimation):
    """Move a simple dot along a province route."""

    def __init__(
        self,
        route: list[int],
        turnaround_index: int,
        speed: float = 220.0,
        pause_duration: float = 0.4,
        color: tuple[int, int, int] = (255, 80, 80),
        radius: int = 10,
    ):
        self.route = route
        self.turnaround_index = turnaround_index
        self.speed = speed
        self.pause_duration = pause_duration
        self.color = color
        self.radius = radius

        self._segment_index = 0
        self._segment_progress = 0.0
        self._pause_remaining = pause_duration
        self._current_position: tuple[float, float] | None = None

    def update(self, dt: float) -> None:
        """Advance the animation state."""
        if len(self.route) < 2:
            return

        if self._pause_remaining > 0:
            self._pause_remaining = max(0.0, self._pause_remaining - dt)
            return

        self._segment_progress += dt * self.speed

    def render(
        self,
        surface: pygame.Surface,
        province_map: UIProvinceMap,
        transform: Transform,
    ) -> None:
        """Render the moving dot at the current interpolated position."""
        if not self.route:
            return

        self._advance_segments(province_map, transform)
        current_position = self._get_current_position(province_map, transform)
        if not current_position:
            return

        self._current_position = current_position
        x, y = int(current_position[0]), int(current_position[1])

        glow_radius = self.radius + 8
        glow = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.color, 90), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow, (x - glow_radius, y - glow_radius))

        pygame.draw.circle(surface, (255, 255, 255), (x, y), self.radius + 2)
        pygame.draw.circle(surface, self.color, (x, y), self.radius)

    def _advance_segments(self, province_map: UIProvinceMap, transform: Transform) -> None:
        """Move through completed route segments and loop the path."""
        while len(self.route) > 1 and self._segment_progress >= self._segment_length(
            province_map, transform, self._segment_index
        ):
            segment_length = self._segment_length(province_map, transform, self._segment_index)
            if segment_length <= 0:
                self._segment_index += 1
            else:
                self._segment_progress -= segment_length
                self._segment_index += 1

            if self._segment_index >= len(self.route) - 1:
                self._segment_index = 0
                self._segment_progress = 0.0
                self._pause_remaining = self.pause_duration
                return

            if self._is_pause_stop():
                self._pause_remaining = self.pause_duration

    def _is_pause_stop(self) -> bool:
        """Pause at the outbound/inbound endpoints for readability."""
        current_stop = self.route[self._segment_index]
        return current_stop in (self.route[0], self.route[self.turnaround_index])

    def _get_current_position(
        self, province_map: UIProvinceMap, transform: Transform
    ) -> tuple[float, float] | None:
        if len(self.route) == 1:
            pos = province_map.get_province_screen_position(
                self.route[0], transform, anchor="number"
            )
            if pos:
                return (float(pos[0]), float(pos[1]))
            return None

        start = province_map.get_province_screen_position(
            self.route[self._segment_index], transform, anchor="number"
        )
        end = province_map.get_province_screen_position(
            self.route[self._segment_index + 1], transform, anchor="number"
        )
        if not start or not end:
            return None

        segment_length = self._segment_length(province_map, transform, self._segment_index)
        if segment_length <= 0:
            return (float(end[0]), float(end[1]))

        t = max(0.0, min(1.0, self._segment_progress / segment_length))
        x = start[0] + (end[0] - start[0]) * t
        y = start[1] + (end[1] - start[1]) * t
        return (x, y)

    def _segment_length(
        self, province_map: UIProvinceMap, transform: Transform, index: int
    ) -> float:
        start = province_map.get_province_screen_position(
            self.route[index], transform, anchor="number"
        )
        end = province_map.get_province_screen_position(
            self.route[index + 1], transform, anchor="number"
        )
        if not start or not end:
            return 0.0
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        return (dx * dx + dy * dy) ** 0.5


def build_round_trip_route(start_province: int, goal_province: int) -> tuple[list[int], list[int]]:
    """Compute an outbound route and exact retrace back to origin."""
    shape_manager = ProvinceShapeManager.get_instance()
    outbound = find_shortest_province_path(start_province, goal_province, shape_manager)
    round_trip = outbound + list(reversed(outbound[:-1]))
    return outbound, round_trip


def main() -> None:
    """Run the province route animation demo."""
    pygame.init()

    screen = pygame.display.set_mode((1280, 800))
    pygame.display.set_caption("Province Route Animation Test")
    clock = pygame.time.Clock()

    manager = UIManager.get_instance()
    manager.actual_resolution = (1280, 800)
    manager.transform = Transform((1280, 800), (1280, 800))

    root_container = UIContainer(
        position=(0, 0),
        size=(1280, 800),
        background_color=(26, 26, 46),
        parent=None,
    )

    province_map = UIProvinceMap(position=(20, 60), size=(1240, 680), parent=root_container)

    outbound_route, round_trip_route = build_round_trip_route(1, 35)
    print(f"Outbound route 1 -> 35: {outbound_route}")
    print(f"Round trip route: {round_trip_route}")

    province_map.set_highlighted_provinces(set(outbound_route))
    province_map.set_province_text_icon(1, "S")
    province_map.set_province_text_icon(35, "G")
    province_map.add_animation(
        ProvinceRouteDotAnimation(round_trip_route, turnaround_index=len(outbound_route) - 1)
    )

    manager.root_component = root_container
    manager.current_screen = root_container

    running = True
    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT or (
                event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE
            ):
                running = False

        manager.update(dt)

        screen.fill((18, 18, 28))
        manager.render(screen)
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
