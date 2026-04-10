"""Map geometry module for province shapes and hit detection."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pygame


@dataclass
class ProvinceShape:
    """Geometric shape for a province on the map.

    Attributes:
        province_id: The province number (1-41)
        name: Human-readable name (e.g., "Youzhou-1")
        points: List of (x, y) polygon vertices in design coordinates
        center: (x, y) center point for unit positioning
        neighbors: List of adjacent province IDs
        terrain_features: List of terrain tags (e.g., "coast_east", "mountain_west")
        number_position: (x, y) position for province number overlay
    """

    province_id: int
    name: str
    points: list[tuple[int, int]]
    center: tuple[int, int]
    neighbors: list[int]
    terrain_features: list[str]
    number_position: tuple[int, int]

    def contains_point(self, x: float, y: float) -> bool:
        """Check if a point is inside this province using ray casting algorithm.

        Args:
            x: X coordinate to test
            y: Y coordinate to test

        Returns:
            True if point is inside the polygon
        """
        # Ray casting algorithm
        n = len(self.points)
        inside = False

        j = n - 1
        for i in range(n):
            xi, yi = self.points[i]
            xj, yj = self.points[j]

            # Check if point is on edge
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                inside = not inside

            j = i

        return inside

    def get_scaled_points(self, scale: float) -> list[tuple[float, float]]:
        """Get polygon points scaled to current resolution.

        Args:
            scale: Scale factor from design resolution

        Returns:
            List of scaled (x, y) tuples
        """
        return [(x * scale, y * scale) for x, y in self.points]

    def get_scaled_center(self, scale: float) -> tuple[float, float]:
        """Get center point scaled to current resolution.

        Args:
            scale: Scale factor from design resolution

        Returns:
            Scaled (x, y) center point
        """
        return (self.center[0] * scale, self.center[1] * scale)

    def get_scaled_number_position(self, scale: float) -> tuple[float, float]:
        """Get number position scaled to current resolution.

        Args:
            scale: Scale factor from design resolution

        Returns:
            Scaled (x, y) position for number overlay
        """
        return (self.number_position[0] * scale, self.number_position[1] * scale)

    def get_bounds(self) -> tuple[int, int, int, int]:
        """Get bounding box for optimization.

        Returns:
            Tuple of (min_x, min_y, max_x, max_y)
        """
        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))

    def distance_to_point(self, x: float, y: float) -> float:
        """Calculate distance from center to a point.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            Euclidean distance
        """
        cx, cy = self.center
        return ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5


class ProvinceShapeManager:
    """Loads and manages province shapes from JSON data.

    This class is a singleton that loads province shape data once
    and provides fast lookup for rendering and hit detection.
    """

    _instance: ProvinceShapeManager | None = None

    def __new__(cls, *args, **kwargs):
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, shapes_file: str | None = None):
        """Initialize the shape manager.

        Args:
            shapes_file: Path to province_shapes.json. If None, uses default.
        """
        if self._initialized:
            return

        self.shapes: dict[int, ProvinceShape] = {}
        self._bounds_index: list[tuple[int, tuple[int, int, int, int]]] = []
        self.map_dimensions = {"width": 1000, "height": 650}
        self.map_offset = {"x": 140, "y": 75}

        if shapes_file is None:
            shapes_file = "data/province_shapes.json"

        self._load_shapes(shapes_file)
        self._initialized = True

    def _load_shapes(self, shapes_file: str) -> None:
        """Load province shapes from JSON file.

        Args:
            shapes_file: Path to JSON file
        """
        file_path = Path(shapes_file)

        if not file_path.exists():
            # Try relative to project root
            file_path = Path("/home/tom/dev/Rotk2_Python") / shapes_file

        if not file_path.exists():
            raise FileNotFoundError(f"Province shapes file not found: {shapes_file}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Load map dimensions
        if "map_dimensions" in data:
            self.map_dimensions = data["map_dimensions"]

        # Load province shapes
        provinces_data = data.get("provinces", {})

        for province_id_str, province_data in provinces_data.items():
            province_id = int(province_id_str)

            shape = ProvinceShape(
                province_id=province_id,
                name=province_data["name"],
                points=[tuple(p) for p in province_data["points"]],
                center=tuple(province_data["center"]),
                neighbors=province_data["neighbors"],
                terrain_features=province_data.get("terrain_features", []),
                number_position=tuple(province_data["number_position"]),
            )

            self.shapes[province_id] = shape
            self._bounds_index.append((province_id, shape.get_bounds()))

        print(f"Loaded {len(self.shapes)} province shapes")

    def get_shape(self, province_id: int) -> ProvinceShape | None:
        """Get shape for a specific province.

        Args:
            province_id: Province number (1-41)

        Returns:
            ProvinceShape or None if not found
        """
        return self.shapes.get(province_id)

    def get_all_shapes(self) -> list[ProvinceShape]:
        """Get all province shapes.

        Returns:
            List of all ProvinceShape objects
        """
        return list(self.shapes.values())

    def get_province_at_point(self, x: float, y: float) -> int | None:
        """Find which province contains the given point.

        Uses bounding box optimization before doing full polygon test.

        Args:
            x: X coordinate in design space
            y: Y coordinate in design space

        Returns:
            Province ID or None if no province contains the point
        """
        # Check bounding boxes first (optimization)
        for province_id, bounds in self._bounds_index:
            min_x, min_y, max_x, max_y = bounds

            if min_x <= x <= max_x and min_y <= y <= max_y:
                # Point is in bounding box, do full polygon test
                shape = self.shapes[province_id]
                if shape.contains_point(x, y):
                    return province_id

        return None

    def get_neighbors(self, province_id: int) -> list[int]:
        """Get adjacent provinces.

        Args:
            province_id: Province number

        Returns:
            List of neighboring province IDs
        """
        shape = self.shapes.get(province_id)
        if shape:
            return shape.neighbors.copy()
        return []

    def get_provinces_by_terrain(self, terrain_feature: str) -> list[int]:
        """Get all provinces with a specific terrain feature.

        Args:
            terrain_feature: Terrain tag to search for

        Returns:
            List of province IDs with that terrain feature
        """
        result = []
        for province_id, shape in self.shapes.items():
            if terrain_feature in shape.terrain_features:
                result.append(province_id)
        return result

    def get_map_size(self) -> tuple[int, int]:
        """Get the design resolution map dimensions.

        Returns:
            Tuple of (width, height)
        """
        return (self.map_dimensions["width"], self.map_dimensions["height"])

    def get_map_offset(self) -> tuple[int, int]:
        """Get the map offset within the screen.

        Returns:
            Tuple of (offset_x, offset_y)
        """
        return (self.map_offset["x"], self.map_offset["y"])

    @classmethod
    def get_instance(cls) -> ProvinceShapeManager:
        """Get the singleton instance.

        Returns:
            ProvinceShapeManager instance
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset the singleton (useful for testing)."""
        cls._instance = None


def test_contains_point():
    """Test the point-in-polygon algorithm."""
    # Create a simple square shape
    shape = ProvinceShape(
        province_id=999,
        name="Test",
        points=[(0, 0), (100, 0), (100, 100), (0, 100)],
        center=(50, 50),
        neighbors=[],
        terrain_features=[],
        number_position=(50, 50),
    )

    # Test points
    assert shape.contains_point(50, 50) == True, "Center should be inside"
    assert shape.contains_point(50, -10) == False, "Outside top"
    assert shape.contains_point(150, 50) == False, "Outside right"
    assert shape.contains_point(1, 1) == True, "Near corner inside"
    # Note: points exactly on edges/vertices may return True or False depending on algorithm

    print("Point-in-polygon tests passed!")


def test_shape_manager():
    """Test loading shapes from file."""
    manager = ProvinceShapeManager()

    # Check we loaded all 41 provinces
    assert len(manager.get_all_shapes()) == 41, "Should have 41 provinces"

    # Check specific province
    shape = manager.get_shape(1)
    assert shape is not None, "Province 1 should exist"
    assert shape.name == "Youzhou-1", f"Expected Youzhou-1, got {shape.name}"
    assert len(shape.points) >= 3, "Should have at least 3 points"
    assert len(shape.neighbors) > 0, "Should have neighbors"

    # Test hit detection on province 1 center
    province_id = manager.get_province_at_point(shape.center[0], shape.center[1])
    assert province_id == 1, f"Center should be in province 1, got {province_id}"

    # Test neighbors
    neighbors = manager.get_neighbors(1)
    assert 2 in neighbors, "Province 1 should neighbor province 2"
    assert 3 in neighbors, "Province 1 should neighbor province 3"

    print("Shape manager tests passed!")


if __name__ == "__main__":
    test_contains_point()
    test_shape_manager()
    print("\nAll tests passed!")
