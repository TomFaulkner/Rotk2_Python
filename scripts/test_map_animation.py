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
from UI.components.map_travel_animation import MapTravelAnimation, TravelDirective, TravelState
from UI.components.province_map import UIProvinceMap
from UI.core.container import UIContainer
from UI.core.manager import UIManager
from UI.core.transform import Transform
from UI.map import ProvinceShapeManager, find_shortest_province_path


def build_round_trip_route(start_province: int, goal_province: int) -> tuple[list[int], list[int]]:
    """Compute an outbound route and exact retrace back to origin."""
    shape_manager = ProvinceShapeManager.get_instance()
    outbound = find_shortest_province_path(start_province, goal_province, shape_manager)
    round_trip = outbound + list(reversed(outbound[:-1]))
    return outbound, round_trip


def demo_on_hop(from_province: int, to_province: int, travel_state: TravelState) -> TravelDirective:
    """Demonstrate a bad event occurring on one hop."""
    if not travel_state.is_returning and from_province == 21 and to_province == 31:
        travel_state.color = (90, 150, 255)
        travel_state.status = "bad_event"
    return TravelDirective.CONTINUE


def demo_on_arrive(province_id: int, travel_state: TravelState) -> TravelDirective:
    """Restore the default color after returning home."""
    if province_id == travel_state.origin_province:
        travel_state.color = (255, 80, 80)
        travel_state.status = "traveling"
    return TravelDirective.CONTINUE


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
        MapTravelAnimation(
            round_trip_route,
            loop=True,
            on_hop=demo_on_hop,
            on_arrive=demo_on_arrive,
            initial_color=(255, 80, 80),
        )
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
