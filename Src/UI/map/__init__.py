"""Map module for SNES-style world map rendering.

This module provides components for rendering and interacting with
the ROTK2 world map, including province shapes, pathfinding, and
unit movement.
"""

from map_geometry import ProvinceShape, ProvinceShapeManager
from map_renderer import MapRenderer

__all__ = [
    "ProvinceShape",
    "ProvinceShapeManager",
    "MapRenderer",
]
