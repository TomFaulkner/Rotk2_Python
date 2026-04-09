"""
Tests for UI core components.
"""

from __future__ import annotations

import pytest
import pygame

# Import UI components
from UI.core.anchor import Anchor, Position, UIMode
from UI.core.transform import Transform
from UI.core.component import UIComponent
from UI.core.container import UIContainer
from UI.core.manager import UIManager
from UI.components.basic import UILabel, UIButton


class TestAnchor:
    """Tests for anchor system."""

    def test_anchor_values(self):
        """Test anchor enum values."""
        assert Anchor.TOP_LEFT.value == "top_left"
        assert Anchor.CENTER.value == "center"
        assert Anchor.BOTTOM_RIGHT.value == "bottom_right"

    def test_position_absolute(self):
        """Test absolute position."""
        pos = Position(100, 200)
        result = pos.resolve((800, 600), (50, 30))
        assert result == (100, 200)

    def test_position_relative(self):
        """Test relative position with percentages."""
        pos = Position("10%", "20%")
        result = pos.resolve((800, 600), (50, 30))
        assert result == (80, 120)  # 10% of 800 = 80, 20% of 600 = 120

    def test_position_anchor_center(self):
        """Test center anchor adjustment."""
        pos = Position(400, 300, anchor=Anchor.CENTER)
        result = pos.resolve((800, 600), (100, 50))
        # Center anchor: x - width/2, y - height/2
        assert result == (350, 275)  # 400 - 50, 300 - 25

    def test_position_anchor_top_right(self):
        """Test top-right anchor adjustment."""
        pos = Position(800, 0, anchor=Anchor.TOP_RIGHT)
        result = pos.resolve((800, 600), (100, 50))
        # Top-right anchor: x - width, y unchanged
        assert result == (700, 0)  # 800 - 100


class TestTransform:
    """Tests for transform/scaling system."""

    def test_transform_same_resolution(self):
        """Test transform with same virtual and actual resolution."""
        transform = Transform((1280, 800), (1280, 800))

        assert transform.scale == 1.0
        assert transform.offset_x == 0
        assert transform.offset_y == 0

        rect = pygame.Rect(100, 100, 200, 150)
        screen_rect = transform.to_screen(rect)
        assert screen_rect == pygame.Rect(100, 100, 200, 150)

    def test_transform_scale_up(self):
        """Test scaling up to higher resolution."""
        transform = Transform((640, 400), (1280, 800))

        assert transform.scale == 2.0

        rect = pygame.Rect(100, 100, 200, 150)
        screen_rect = transform.to_screen(rect)
        assert screen_rect == pygame.Rect(200, 200, 400, 300)

    def test_transform_scale_down(self):
        """Test scaling down to lower resolution."""
        transform = Transform((1280, 800), (640, 400))

        assert transform.scale == 0.5

        rect = pygame.Rect(100, 100, 200, 150)
        screen_rect = transform.to_screen(rect)
        assert screen_rect == pygame.Rect(50, 50, 100, 75)

    def test_transform_letterboxing(self):
        """Test letterboxing for different aspect ratios."""
        # 16:10 virtual to 16:9 actual
        transform = Transform((1280, 800), (1920, 1080))

        # Should maintain aspect ratio
        assert transform.scale <= 1.35  # Less than or equal to full width scale
        assert transform.offset_x > 0  # Horizontal letterbox

    def test_to_virtual(self):
        """Test converting screen coordinates to virtual."""
        transform = Transform((640, 400), (1280, 800))

        # Screen point (200, 200) should be virtual (100, 100) at 2x scale
        virtual = transform.to_virtual((200, 200))
        assert virtual == (100.0, 100.0)

    def test_scale_distance(self):
        """Test scaling distances."""
        transform = Transform((640, 400), (1280, 800))

        # At 2x scale, distance of 10 becomes 20
        assert transform.scale_distance(10) == 20


class TestPosition:
    """Tests for Position class."""

    def test_position_str(self):
        """Test position string representation."""
        pos = Position(100, 200, anchor=Anchor.CENTER)
        repr_str = repr(pos)
        assert "100" in repr_str
        assert "200" in repr_str
        assert "center" in repr_str


@pytest.fixture(autouse=True)
def init_pygame():
    """Initialize pygame for all tests."""
    pygame.init()
    pygame.font.init()
    yield
    pygame.quit()


class TestUIContainer:
    """Tests for UIContainer."""

    def test_container_creation(self):
        """Test creating a container."""
        container = UIContainer(position=(0, 0), size=(400, 300), background_color=(100, 100, 100))

        assert container.size == (400, 300)
        assert container.background_color == (100, 100, 100)
        assert len(container.children) == 0

    def test_add_child(self):
        """Test adding children to container."""
        container = UIContainer(size=(400, 300))
        child = UILabel(text="Test", position=(10, 10))

        container.add_child(child)

        assert len(container.children) == 1
        assert child in container.children
        assert child.parent == container

    def test_remove_child(self):
        """Test removing children from container."""
        container = UIContainer(size=(400, 300))
        child = UILabel(text="Test")

        container.add_child(child)
        container.remove_child(child)

        assert len(container.children) == 0
        assert child.parent is None

    def test_content_rect(self):
        """Test content rectangle calculation."""
        container = UIContainer(
            position=(0, 0),
            size=(400, 300),
            padding=(10, 20, 10, 20),  # top, right, bottom, left
        )

        content = container.get_content_rect()

        assert content.x == 20  # left padding
        assert content.y == 10  # top padding
        assert content.width == 360  # 400 - 20 - 20
        assert content.height == 280  # 300 - 10 - 10

    def test_clear_children(self):
        """Test clearing all children."""
        container = UIContainer(size=(400, 300))
        child1 = UILabel(text="Child 1")
        child2 = UILabel(text="Child 2")

        container.add_child(child1)
        container.add_child(child2)
        container.clear_children()

        assert len(container.children) == 0
        assert child1.parent is None
        assert child2.parent is None


class TestUIManager:
    """Tests for UIManager singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        UIManager.reset_instance()

    def test_singleton(self):
        """Test that UIManager is a singleton."""
        manager1 = UIManager()
        manager2 = UIManager()

        assert manager1 is manager2

    def test_get_instance(self):
        """Test get_instance method."""
        manager1 = UIManager.get_instance()
        manager2 = UIManager.get_instance()

        assert manager1 is manager2

    def test_default_resolution(self):
        """Test default virtual resolution."""
        manager = UIManager()

        assert manager.virtual_resolution == (1280, 800)
        assert manager.mode == UIMode.MODERN

    def test_set_mode_classic(self):
        """Test setting classic mode."""
        manager = UIManager()
        manager.set_mode(UIMode.CLASSIC)

        assert manager.mode == UIMode.CLASSIC
        assert manager.virtual_resolution == (640, 400)

    def test_set_resolution(self):
        """Test changing actual resolution."""
        manager = UIManager()
        manager.set_resolution(1920, 1080)

        assert manager.actual_resolution == (1920, 1080)
        assert manager.transform.scale > 1.0  # Should scale up


class TestUILabel:
    """Tests for UILabel."""

    def test_label_creation(self):
        """Test creating a label."""
        label = UILabel(text="Hello", position=(10, 20), size=(100, 30))

        assert label.text == "Hello"
        assert label.rect.topleft == (10, 20)

    def test_label_text_change(self):
        """Test changing label text."""
        label = UILabel(text="Hello")
        label.text = "World"

        assert label.text == "World"
        assert label._needs_render is True

    def test_label_alignment(self):
        """Test label alignment options."""
        label_left = UILabel(text="Test", align="left")
        label_center = UILabel(text="Test", align="center")
        label_right = UILabel(text="Test", align="right")

        assert label_left.align == "left"
        assert label_center.align == "center"
        assert label_right.align == "right"


class TestUIButton:
    """Tests for UIButton."""

    def test_button_creation(self):
        """Test creating a button."""
        clicked = False

        def on_click():
            nonlocal clicked
            clicked = True

        button = UIButton(text="Click Me", on_click=on_click, position=(0, 0), size=(100, 40))

        assert button.text == "Click Me"
        assert button.on_click is on_click
        assert len(button.children) == 1  # Has label child

    def test_button_states(self):
        """Test button state management."""
        button = UIButton(text="Test")

        assert button._hovered is False
        assert button._pressed is False

        button.on_mouse_enter()
        assert button._hovered is True

        button.on_mouse_leave()
        assert button._hovered is False
        assert button._pressed is False


# Skip pygame display-dependent tests in headless environments
@pytest.mark.skipif(not pygame.display.get_init(), reason="Pygame display not initialized")
class TestUIRendering:
    """Tests that require pygame display."""

    def test_label_preferred_size(self):
        """Test getting label preferred size."""
        pygame.font.init()
        label = UILabel(text="Test")
        size = label.get_preferred_size()

        assert size[0] > 0
        assert size[1] > 0
