"""Tests for the UI map module."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from map_geometry import ProvinceShape, ProvinceShapeManager
from map_renderer import MapRenderer


class TestProvinceShape:
    """Tests for ProvinceShape class."""

    @pytest.fixture
    def sample_shape(self):
        """Create a sample square shape for testing."""
        return ProvinceShape(
            province_id=1,
            name="Test Province",
            points=[(0, 0), (100, 0), (100, 100), (0, 100)],
            center=(50, 50),
            neighbors=[2, 3],
            terrain_features=["coast_east"],
            number_position=(50, 50),
        )

    def test_contains_point_center(self, sample_shape):
        """Test that center point is inside."""
        assert sample_shape.contains_point(50, 50) is True

    def test_contains_point_inside(self, sample_shape):
        """Test that points inside are detected."""
        assert sample_shape.contains_point(25, 25) is True
        assert sample_shape.contains_point(75, 75) is True

    def test_contains_point_outside(self, sample_shape):
        """Test that points outside are not detected."""
        assert sample_shape.contains_point(150, 50) is False
        assert sample_shape.contains_point(50, -50) is False
        assert sample_shape.contains_point(150, 150) is False

    def test_get_scaled_points(self, sample_shape):
        """Test point scaling."""
        scaled = sample_shape.get_scaled_points(2.0)
        assert scaled == [(0, 0), (200, 0), (200, 200), (0, 200)]

    def test_get_scaled_center(self, sample_shape):
        """Test center scaling."""
        scaled = sample_shape.get_scaled_center(2.0)
        assert scaled == (100, 100)

    def test_get_bounds(self, sample_shape):
        """Test bounding box calculation."""
        bounds = sample_shape.get_bounds()
        assert bounds == (0, 0, 100, 100)

    def test_distance_to_point(self, sample_shape):
        """Test distance calculation."""
        # Distance from center (50,50) to (100,50) should be 50
        assert sample_shape.distance_to_point(100, 50) == 50.0


class TestProvinceShapeManager:
    """Tests for ProvinceShapeManager class."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test."""
        ProvinceShapeManager.reset_instance()
        yield
        ProvinceShapeManager.reset_instance()

    def test_singleton_pattern(self):
        """Test that manager is a singleton."""
        manager1 = ProvinceShapeManager()
        manager2 = ProvinceShapeManager()
        assert manager1 is manager2

    def test_load_all_provinces(self):
        """Test that all 41 provinces are loaded."""
        manager = ProvinceShapeManager()
        assert len(manager.get_all_shapes()) == 41

    def test_get_shape_valid(self):
        """Test getting a valid province shape."""
        manager = ProvinceShapeManager()
        shape = manager.get_shape(1)
        assert shape is not None
        assert shape.province_id == 1
        assert shape.name.startswith("Province")

    def test_get_shape_invalid(self):
        """Test getting an invalid province."""
        manager = ProvinceShapeManager()
        assert manager.get_shape(999) is None

    def test_get_province_at_point(self):
        """Test hit detection."""
        manager = ProvinceShapeManager()

        # Find a point that's actually inside province 1
        shape = manager.get_shape(1)
        min_x, min_y, max_x, max_y = shape.get_bounds()

        # Try a grid of points within the bounding box
        found = False
        for x in range(min_x + 10, max_x - 10, 10):
            for y in range(min_y + 10, max_y - 10, 10):
                if shape.contains_point(x, y):
                    province_id = manager.get_province_at_point(x, y)
                    if province_id == 1:
                        found = True
                        break
            if found:
                break

        assert found, "Could not find a point inside province 1"

    def test_get_neighbors(self):
        """Test getting neighbors."""
        manager = ProvinceShapeManager()
        neighbors = manager.get_neighbors(1)
        assert 2 in neighbors
        assert 3 in neighbors

    def test_get_provinces_by_terrain(self):
        """Test terrain-based queries."""
        manager = ProvinceShapeManager()

        # Skip if no terrain data
        all_provinces = manager.get_all_shapes()
        has_terrain = any(p.terrain_features for p in all_provinces)

        if not has_terrain:
            pytest.skip("No terrain data available")

    def test_get_map_size(self):
        """Test map dimensions."""
        manager = ProvinceShapeManager()
        size = manager.get_map_size()
        # Updated to match extracted image dimensions
        assert size == (1024, 896)


class TestMapRenderer:
    """Tests for MapRenderer class."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test."""
        ProvinceShapeManager.reset_instance()
        yield
        ProvinceShapeManager.reset_instance()

    def test_init(self):
        """Test renderer initialization."""
        renderer = MapRenderer()
        assert renderer.design_width == 1000
        assert renderer.design_height == 650
        assert len(renderer.province_rulers) == 41

    def test_set_province_ruler(self):
        """Test setting ruler colors."""
        renderer = MapRenderer()

        # Set ruler
        renderer.set_province_ruler(1, 5)
        assert renderer.province_rulers[1] == 5

        # Set to unruled
        renderer.set_province_ruler(1, None)
        assert renderer.province_rulers[1] == -1

        # Set to unruled with -1
        renderer.set_province_ruler(1, -1)
        assert renderer.province_rulers[1] == -1

    def test_set_province_ruler_invalid(self):
        """Test setting ruler for invalid province."""
        renderer = MapRenderer()

        # Should not raise, just print warning
        renderer.set_province_ruler(999, 0)
        assert 999 not in renderer.province_rulers

    def test_highlight_province(self):
        """Test province highlighting."""
        renderer = MapRenderer()

        renderer.highlight_province(5)
        assert renderer.highlighted_province == 5

        renderer.highlight_province(None)
        assert renderer.highlighted_province is None

    def test_set_show_numbers(self):
        """Test toggling numbers."""
        renderer = MapRenderer()

        assert renderer.show_numbers is True
        renderer.set_show_numbers(False)
        assert renderer.show_numbers is False

    def test_get_ruler_color_valid(self):
        """Test getting valid ruler colors."""
        renderer = MapRenderer()

        color = renderer._get_ruler_color(0)
        assert color == (170, 170, 170)  # Gray

        color = renderer._get_ruler_color(1)
        assert color == (255, 255, 85)  # Yellow

    def test_get_ruler_color_unruled(self):
        """Test getting color for unruled province."""
        renderer = MapRenderer()

        color = renderer._get_ruler_color(-1)
        assert color is None

    def test_get_ruler_color_invalid(self):
        """Test getting color for invalid ruler."""
        renderer = MapRenderer()

        color = renderer._get_ruler_color(99)
        assert color is None

    def test_set_rulers_from_game_state(self):
        """Test bulk ruler update."""
        renderer = MapRenderer()

        game_state = {
            1: 0,
            2: 1,
            3: None,
            4: -1,
        }

        renderer.set_rulers_from_game_state(game_state)

        assert renderer.province_rulers[1] == 0
        assert renderer.province_rulers[2] == 1
        assert renderer.province_rulers[3] == -1
        assert renderer.province_rulers[4] == -1


class TestDataConsistency:
    """Tests to verify data file consistency."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Reset singleton before each test."""
        ProvinceShapeManager.reset_instance()
        yield
        ProvinceShapeManager.reset_instance()

    def test_all_provinces_have_valid_data(self):
        """Test that all provinces have valid shape data."""
        manager = ProvinceShapeManager()

        for province_id in range(1, 42):
            shape = manager.get_shape(province_id)
            assert shape is not None, f"Province {province_id} missing"
            assert len(shape.points) >= 3, f"Province {province_id} has fewer than 3 points"
            assert shape.center[0] > 0 and shape.center[1] > 0

    def test_neighbors_are_bidirectional(self):
        """Test that neighbor relationships are bidirectional."""
        manager = ProvinceShapeManager()

        for province_id in range(1, 42):
            shape = manager.get_shape(province_id)
            for neighbor_id in shape.neighbors:
                neighbor = manager.get_shape(neighbor_id)
                assert province_id in neighbor.neighbors, (
                    f"Province {province_id} lists {neighbor_id} as neighbor but not vice versa"
                )

    def test_provinces_json_exists(self):
        """Test that the shapes JSON file exists."""
        json_path = Path("/home/tom/dev/Rotk2_Python/data/province_shapes.json")
        assert json_path.exists()

        with open(json_path, "r") as f:
            data = json.load(f)

        assert "provinces" in data
        assert len(data["provinces"]) == 41


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
