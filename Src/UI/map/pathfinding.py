"""Province adjacency pathfinding helpers."""

from __future__ import annotations

from collections import deque

from .map_geometry import ProvinceShapeManager


def find_shortest_province_path(
    start_province: int,
    goal_province: int,
    shape_manager: ProvinceShapeManager | None = None,
    allowed_provinces: set[int] | None = None,
) -> list[int]:
    """Find the shortest province path using adjacency BFS.

    Args:
        start_province: Starting province number
        goal_province: Destination province number
        shape_manager: Optional shape manager instance
        allowed_provinces: Optional province whitelist for traversal

    Returns:
        List of province IDs from start to goal, inclusive

    Raises:
        ValueError: If start/goal are invalid or no route exists
    """
    manager = shape_manager or ProvinceShapeManager.get_instance()

    if manager.get_shape(start_province) is None:
        raise ValueError(f"Unknown start province: {start_province}")
    if manager.get_shape(goal_province) is None:
        raise ValueError(f"Unknown goal province: {goal_province}")

    if allowed_provinces is not None and (
        start_province not in allowed_provinces or goal_province not in allowed_provinces
    ):
        raise ValueError("Start and goal provinces must be within allowed_provinces")

    if start_province == goal_province:
        return [start_province]

    frontier: deque[int] = deque([start_province])
    previous: dict[int, int | None] = {start_province: None}

    while frontier:
        current = frontier.popleft()
        neighbors = sorted(manager.get_neighbors(current))

        for neighbor in neighbors:
            if allowed_provinces is not None and neighbor not in allowed_provinces:
                continue
            if neighbor in previous:
                continue

            previous[neighbor] = current
            if neighbor == goal_province:
                return _reconstruct_path(previous, goal_province)
            frontier.append(neighbor)

    raise ValueError(f"No path found from province {start_province} to {goal_province}")


def _reconstruct_path(previous: dict[int, int | None], goal_province: int) -> list[int]:
    """Rebuild a BFS path from the predecessor map."""
    path: list[int] = []
    current: int | None = goal_province

    while current is not None:
        path.append(current)
        current = previous[current]

    path.reverse()
    return path
