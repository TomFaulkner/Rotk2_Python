"""Reusable province-to-province travel animation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import pygame

from UI.components.province_map import ProvinceMapAnimation

if TYPE_CHECKING:
    from UI.components.province_map import UIProvinceMap
    from UI.core.transform import Transform


class TravelDirective(Enum):
    """Control flow returned from travel callbacks."""

    CONTINUE = "continue"
    ABORT = "abort"
    RETURN_TO_ORIGIN = "return_to_origin"


@dataclass
class TravelState:
    """Mutable state shared with travel callbacks."""

    origin_province: int
    destination_province: int
    current_province: int
    planned_route: list[int]
    traversed_provinces: list[int] = field(default_factory=list)
    color: tuple[int, int, int] = (255, 80, 80)
    status: str = "traveling"
    is_returning: bool = False


HopCallback = Callable[[int, int, TravelState], TravelDirective | None]
ArrivalCallback = Callable[[int, TravelState], TravelDirective | None]


class MapTravelAnimation(ProvinceMapAnimation):
    """Animate travel along a province route with hop and arrival callbacks."""

    def __init__(
        self,
        route: list[int],
        speed: float = 220.0,
        pause_duration: float = 0.4,
        radius: int = 10,
        loop: bool = False,
        on_hop: HopCallback | None = None,
        on_arrive: ArrivalCallback | None = None,
        initial_color: tuple[int, int, int] = (255, 80, 80),
    ):
        if not route:
            raise ValueError("Travel route must contain at least one province")

        self._base_route = route[:]
        self._active_route = route[:]
        self.speed = speed
        self.pause_duration = pause_duration
        self.radius = radius
        self.loop = loop
        self.on_hop = on_hop
        self.on_arrive = on_arrive

        self.state = TravelState(
            origin_province=route[0],
            destination_province=route[-1],
            current_province=route[0],
            planned_route=route[:],
            traversed_provinces=[route[0]],
            color=initial_color,
        )

        self._segment_index = 0
        self._segment_progress = 0.0
        self._pause_remaining = pause_duration
        self._current_position: tuple[float, float] | None = None
        self._travel_active = True

    def update(self, dt: float) -> None:
        """Advance travel along the current route."""
        if not self._travel_active or len(self._active_route) < 2:
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
        """Render the travel marker at its interpolated position."""
        current_position = self._get_current_position(province_map, transform)
        if current_position is None:
            return

        self._current_position = current_position
        self._advance_segments(province_map, transform)

        x, y = int(self._current_position[0]), int(self._current_position[1])
        glow_radius = self.radius + 8
        glow = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*self.state.color, 90), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow, (x - glow_radius, y - glow_radius))

        pygame.draw.circle(surface, (255, 255, 255), (x, y), self.radius + 2)
        pygame.draw.circle(surface, self.state.color, (x, y), self.radius)

    def reset(self) -> None:
        """Reset the animation back to its original route."""
        self._active_route = self._base_route[:]
        self._segment_index = 0
        self._segment_progress = 0.0
        self._pause_remaining = self.pause_duration
        self.state.current_province = self._base_route[0]
        self.state.destination_province = self._base_route[-1]
        self.state.planned_route = self._base_route[:]
        self.state.traversed_provinces = [self._base_route[0]]
        self.state.status = "traveling"
        self.state.is_returning = False
        self._travel_active = True

    def _get_current_position(
        self, province_map: UIProvinceMap, transform: Transform
    ) -> tuple[float, float] | None:
        if len(self._active_route) == 1:
            pos = province_map.get_province_screen_position(
                self._active_route[0], transform, anchor="number"
            )
            if pos:
                return (float(pos[0]), float(pos[1]))
            return None

        start = province_map.get_province_screen_position(
            self._active_route[self._segment_index], transform, anchor="number"
        )
        end = province_map.get_province_screen_position(
            self._active_route[self._segment_index + 1], transform, anchor="number"
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

    def _advance_segments(self, province_map: UIProvinceMap, transform: Transform) -> None:
        while self._travel_active and len(self._active_route) > 1:
            segment_length = self._segment_length(province_map, transform, self._segment_index)
            if self._segment_progress < segment_length:
                return

            self._segment_progress = max(0.0, self._segment_progress - segment_length)
            from_province = self._active_route[self._segment_index]
            to_province = self._active_route[self._segment_index + 1]

            hop_directive = self._invoke_hop_callback(from_province, to_province)
            if self._apply_directive(hop_directive):
                return

            self.state.current_province = to_province
            self.state.traversed_provinces.append(to_province)

            arrival_directive = self._invoke_arrival_callback(to_province)
            if self._apply_directive(arrival_directive):
                return

            self._segment_index += 1
            self._pause_remaining = self.pause_duration

            if self._segment_index >= len(self._active_route) - 1:
                if self.loop:
                    self.reset()
                else:
                    self.state.status = "completed"
                    self._travel_active = False
                return

    def _invoke_hop_callback(self, from_province: int, to_province: int) -> TravelDirective | None:
        if self.on_hop is None:
            return None
        return self.on_hop(from_province, to_province, self.state)

    def _invoke_arrival_callback(self, province_id: int) -> TravelDirective | None:
        if self.on_arrive is None:
            return None
        return self.on_arrive(province_id, self.state)

    def _apply_directive(self, directive: TravelDirective | None) -> bool:
        if directive is None or directive == TravelDirective.CONTINUE:
            return False

        if directive == TravelDirective.ABORT:
            self.state.status = "aborted"
            self._travel_active = False
            return True

        if directive == TravelDirective.RETURN_TO_ORIGIN:
            self._start_return_trip()
            return True

        return False

    def _start_return_trip(self) -> None:
        if self.state.is_returning:
            self.state.status = "aborted"
            self._travel_active = False
            return

        return_route = list(reversed(self.state.traversed_provinces))
        if len(return_route) < 2:
            self.state.status = "aborted"
            self._travel_active = False
            return

        self._active_route = return_route
        self._segment_index = 0
        self._segment_progress = 0.0
        self._pause_remaining = self.pause_duration
        self.state.is_returning = True
        self.state.destination_province = self.state.origin_province
        self.state.planned_route = return_route[:]
        self.state.status = "traveling"
        self._travel_active = True

    def _segment_length(
        self, province_map: UIProvinceMap, transform: Transform, index: int
    ) -> float:
        start = province_map.get_province_screen_position(
            self._active_route[index], transform, anchor="number"
        )
        end = province_map.get_province_screen_position(
            self._active_route[index + 1], transform, anchor="number"
        )
        if not start or not end:
            return 0.0
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        return (dx * dx + dy * dy) ** 0.5
