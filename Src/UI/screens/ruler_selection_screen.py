"""
Ruler Selection Screen for ROTK2 - Popup Overlay Design

Interactive map-based ruler selection with popup overlay.
Features:
- Full-screen interactive world map
- Click on a province OR use keyboard/gamepad to navigate
- Popup shows ruler info over the map
- Keyboard/Gamepad: Arrow keys/D-pad to cycle provinces, A/Enter to select

Layout:
┌────────────────────────────────────────────┐
│  Select Your Ruler - Click or Navigate       │
├────────────────────────────────────────────┤
│                                             │
│  ┌─────────────────────────────────────────┐│
│  │                                         ││
│  │         [FULL SCREEN WORLD MAP]         ││
│  │                                         ││
│  │  Provinces shown with ruler colors     ││
│  │  Selected province highlighted         ││
│  │                                         ││
│  │  [POPUP - appears when province         ││
│  │   selected]:                            ││
│  │   ┌─────────────────────────────────┐  ││
│  │   │  [Portrait]  Ruler Name         │  ││
│  │   │            Officers: X          │  ││
│  │   │            Soldiers: X            │  ││
│  │   │            [Confirm] [Cancel]   │  ││
│  │   └─────────────────────────────────┘  ││
│  │                                         ││
│  └─────────────────────────────────────────┘│
│                                             │
│  [🎲 Random]  [← Back]                     │
└────────────────────────────────────────────┘
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import pygame

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from UI.core.anchor import Anchor
from UI.core.container import UIContainer
from UI.components.basic import UILabel, UIButton
from UI.components.multiline_label import UIMultiLineLabel
from UI.components.image import UIImage
from UI.core.manager import UIManager
from UI.map.map_renderer import MapRenderer
from UI.screens.snes_province_screen import SnesPortraitLoader

if TYPE_CHECKING:
    pass


class RulerSelectionScreen(UIContainer):
    """
    Ruler selection screen with full-screen map and popup overlay.

    Features:
    - Full-screen interactive world map
    - Click to select OR keyboard/gamepad navigation
    - Popup overlay with ruler info
    - Navigate provinces with arrows/D-pad
    """

    # Tell UIManager we handle our own keyboard/gamepad navigation
    handles_own_navigation = True

    # Navigation modes
    NAV_MODE_ADJACENCY = "adjacency"  # Jump between adjacent provinces
    NAV_MODE_CURSOR = "cursor"  # Free cursor movement like mouse

    # Visual constants
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 800

    # Colors
    BG_COLOR = (26, 26, 46)
    PANEL_COLOR = (22, 33, 62)
    POPUP_COLOR = (30, 35, 55)
    TITLE_COLOR = (255, 215, 0)
    BUTTON_NORMAL = (60, 60, 80)
    BUTTON_HOVER = (80, 80, 110)
    BUTTON_SELECT = (79, 189, 186)
    TEXT_COLOR = (232, 232, 232)
    HIGHLIGHT_COLOR = (100, 200, 100)
    HIGHLIGHT_BORDER = (255, 255, 100)

    # Sample ruler bios
    RULER_BIOS = {
        "Cao Cao": "The cunning warlord who would unite northern China. Known for his strategic brilliance and ruthless efficiency.",
        "Liu Bei": "A virtuous leader who claims descent from the imperial Han. His charisma attracts loyal heroes like Guan Yu and Zhang Fei.",
        "Sun Quan": "The young ruler of Wu, inheriting a strong foundation. He commands the rich Yangtze River region and powerful navy.",
        "Yuan Shao": "The powerful northern warlord with the largest territory. His indecisiveness belies his massive military strength.",
        "Dong Zhuo": "The tyrant who seized control of Luoyang and the Emperor. His cruelty sparked the coalition against him.",
        "Ma Teng": "The western warlord commanding the cavalry of Liang province. A fierce warrior loyal to the Han dynasty.",
        "Liu Biao": "The scholarly governor of Jing province. His territory is prosperous but his indecision leaves him vulnerable.",
        "Liu Zhang": "The weak ruler of Yi province. His land is rich and defensible, but he lacks military ambition.",
    }

    # Ruler name to officer ID mapping (for portrait loading)
    # Based on portrait_mapping.json
    RULER_OFFICER_IDS = {
        "Cao Cao": 0,
        "Liu Bei": 1,
        "Sun Quan": 220,
        "Yuan Shao": 3,
        "Dong Zhuo": 8,
        "Ma Teng": 5,
        "Liu Biao": 7,
        "Liu Zhang": 18,
    }

    def __init__(self):
        """Initialize the ruler selection screen."""
        super().__init__(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, self.SCREEN_HEIGHT),
            background_color=self.BG_COLOR,
            parent=None,
        )

        self._selected_province: int | None = None
        self._selected_ruler: str | None = None
        self._callback: Callable[[str | None], None] | None = None
        self._showing_popup: bool = False

        # Province navigation for keyboard/gamepad
        self._province_cycle_index: int = 0
        self._playable_provinces: list[int] = list(range(1, 42))  # All 41 provinces
        self._nav_mode: str = self.NAV_MODE_ADJACENCY  # Current navigation mode
        self._free_cursor_pos: tuple[float, float] = (640, 400)  # For cursor mode (screen coords)
        self._free_cursor_speed: float = 12.0  # Pixels per frame for cursor movement

        # Key repeat handling for cursor mode
        self._key_states: dict[int, bool] = {}  # Track which keys are held
        self._key_repeat_delay: float = 0.15  # Seconds before repeat starts
        self._key_repeat_interval: float = 0.05  # Seconds between repeats
        self._key_press_times: dict[int, float] = {}  # When key was first pressed
        self._key_last_repeat: dict[int, float] = {}  # Last time key repeated

        # Focus management for popup
        self._popup_buttons: list[UIButton] = []
        self._focused_popup_button: int = 0  # 0 = Select, 1 = Cancel

        # Portrait loader for ruler portraits
        # Get absolute path to Resources directory
        resources_path = Path(__file__).parent.parent.parent.parent / "Resources"
        self._portrait_loader = SnesPortraitLoader(str(resources_path))
        self._portrait_image: UIImage | None = None

        # Create UI elements
        self._create_title()
        self._create_map()
        self._create_popup()  # Hidden initially
        self._create_bottom_buttons()

        # Register with UIManager
        self._register_with_manager()

    def _register_with_manager(self) -> None:
        """Register this screen with the UIManager."""
        try:
            manager = UIManager.get_instance()
            if manager:
                manager.root_component = self
        except Exception as e:
            print(f"Warning: Could not register with UIManager: {e}")

    def _create_title(self) -> None:
        """Create the title bar."""
        title_panel = UIContainer(
            position=(0, 0),
            size=(self.SCREEN_WIDTH, 50),
            background_color=self.PANEL_COLOR,
            border_color=(79, 189, 186),
            border_width=2,
            parent=self,
        )

        title_label = UILabel(
            text="Select Your Ruler - Click on Map or Use ↑↓←→ to Navigate",
            position=(self.SCREEN_WIDTH // 2, 25),
            size=(1000, 40),
            font=pygame.font.Font(None, 36),
            color=self.TITLE_COLOR,
            align="center",
            anchor=Anchor.CENTER,
            parent=self,
        )

    def _create_map(self) -> None:
        """Create the full-screen interactive world map."""
        # Map takes up most of screen below title
        map_x = 20
        map_y = 60
        map_width = 1240
        map_height = 680

        # Map container
        self._map_container = UIContainer(
            position=(map_x, map_y),
            size=(map_width, map_height),
            background_color=(40, 40, 60),
            border_color=(79, 189, 186),
            border_width=2,
            parent=self,
        )

        # Create map renderer
        self.map_renderer = MapRenderer()

        # Load province background
        bg_path = Path(__file__).parent.parent.parent.parent / "download" / "numbers-removed.jpg"
        bg_loaded = self.map_renderer.load_terrain_background(str(bg_path))
        if bg_loaded:
            print("✓ Map background loaded")

        # Set sample rulers with different colors for demo
        sample_rulers = [
            (1, 0, "Cao Cao"),
            (2, 1, "Liu Bei"),
            (3, 2, "Sun Quan"),
            (4, 6, "Yuan Shao"),
            (5, 3, "Dong Zhuo"),
            (6, 7, "Ma Teng"),
            (7, 9, "Liu Biao"),
            (8, 12, "Liu Zhang"),
        ]

        for province_id, ruler_no, ruler_name in sample_rulers:
            self.map_renderer.set_province_ruler(province_id, ruler_no)

        # Store map area for hit detection
        self._map_rect = pygame.Rect(map_x, map_y, map_width, map_height)
        self._map_offset = (map_x, map_y)

        # Cursor for keyboard/gamepad navigation
        self._cursor_visible = False
        self._cursor_pos: tuple[int, int] = (0, 0)  # Screen coordinates
        self._cursor_target_province: int | None = None

    def _create_popup(self) -> None:
        """Create the ruler info popup (initially hidden)."""
        popup_width = 450
        popup_height = 320
        popup_x = (self.SCREEN_WIDTH - popup_width) // 2
        popup_y = (self.SCREEN_HEIGHT - popup_height) // 2

        # Popup container - positioned at center
        self._popup = UIContainer(
            position=(popup_x, popup_y),
            size=(popup_width, popup_height),
            background_color=self.POPUP_COLOR,
            border_color=(255, 255, 255),
            border_width=3,
            padding=20,
            parent=self,
        )
        self._popup.visible = False  # Hidden initially

        # Portrait area - positioned inside popup (relative coords)
        portrait_size = 110
        self._portrait_area = UIContainer(
            position=(20, 20),  # Relative to popup
            size=(portrait_size, portrait_size),
            background_color=(50, 50, 70),
            border_color=(100, 100, 120),
            border_width=2,
            parent=self._popup,
        )

        # Portrait image (will be set when ruler is selected)
        self._portrait_image = None

        # Ruler name - to the right of portrait
        self._popup_ruler_name = UILabel(
            text="Select a Province",
            position=(20 + portrait_size + 15, 25),
            size=(popup_width - portrait_size - 55, 35),
            font=pygame.font.Font(None, 28),
            color=self.TITLE_COLOR,
            align="left",
            parent=self._popup,
        )

        # Province info - below ruler name
        self._popup_province = UILabel(
            text="Use arrow keys or click",
            position=(20 + portrait_size + 15, 65),
            size=(popup_width - portrait_size - 55, 25),
            font=pygame.font.Font(None, 20),
            color=(180, 180, 180),
            align="left",
            parent=self._popup,
        )

        # Stats - below province info (using multi-line for proper newline handling)
        self._popup_stats = UIMultiLineLabel(
            text="Officers: -\nSoldiers: -",
            position=(20 + portrait_size + 15, 95),
            size=(popup_width - portrait_size - 55, 50),
            font=pygame.font.Font(None, 20),
            color=self.HIGHLIGHT_COLOR,
            align="left",
            parent=self._popup,
        )

        # Bio - below portrait (full width, using multi-line with wrapping)
        self._popup_bio = UIMultiLineLabel(
            text="Navigate to a province to see ruler information.",
            position=(20, 145),
            size=(popup_width - 40, 90),
            font=pygame.font.Font(None, 20),  # Smaller font for better fit
            color=self.TEXT_COLOR,
            align="left",
            line_spacing=2,
            parent=self._popup,
        )

        # Confirm button - bottom left
        self._popup_select_btn = UIButton(
            text="✓ Select",
            position=(popup_width // 2 - 100, popup_height - 55),
            size=(90, 40),
            normal_color=self.BUTTON_SELECT,
            hover_color=(100, 210, 200),
            text_color=(0, 0, 0),
            font=pygame.font.Font(None, 22),
            on_click=self._on_confirm_selection,
            parent=self._popup,
        )

        # Cancel button - bottom right
        self._popup_cancel_btn = UIButton(
            text="✕ Cancel",
            position=(popup_width // 2 + 10, popup_height - 55),
            size=(90, 40),
            normal_color=(100, 60, 60),
            hover_color=(120, 80, 80),
            text_color=self.TEXT_COLOR,
            font=pygame.font.Font(None, 22),
            on_click=self._on_cancel_popup,
            parent=self._popup,
        )

        # Store popup buttons for focus navigation
        self._popup_buttons = [self._popup_select_btn, self._popup_cancel_btn]

    def _create_bottom_buttons(self) -> None:
        """Create bottom action buttons."""
        button_y = self.SCREEN_HEIGHT - 50
        button_width = 150
        button_height = 40

        # Random button
        random_btn = UIButton(
            text="🎲 Random",
            position=(30, button_y),
            size=(button_width, button_height),
            normal_color=(100, 80, 120),
            hover_color=(120, 100, 140),
            text_color=self.TEXT_COLOR,
            font=pygame.font.Font(None, 22),
            on_click=self._on_random,
            parent=self,
        )

        # Back button
        back_btn = UIButton(
            text="← Back",
            position=(self.SCREEN_WIDTH - 30 - button_width, button_y),
            size=(button_width, button_height),
            normal_color=self.BUTTON_NORMAL,
            hover_color=self.BUTTON_HOVER,
            text_color=self.TEXT_COLOR,
            font=pygame.font.Font(None, 22),
            on_click=self._on_back,
            parent=self,
        )

    def _on_map_click(self, screen_x: int, screen_y: int, transform=None) -> None:
        """Handle click on the map."""
        # Try to determine which province was clicked using map_renderer
        try:
            from UI.core.manager import UIManager

            manager = UIManager.get_instance()
            if manager and manager.transform:
                province_id = self.map_renderer.get_province_at_screen_point(
                    (screen_x, screen_y), manager.transform
                )
                if province_id:
                    self._navigate_to_province(province_id)
                else:
                    # Clicked on map but not on a province - just cycle
                    self._navigate_by_index(1)
            else:
                # Fallback: just cycle
                self._navigate_by_index(1)
        except Exception as e:
            print(f"Map click error: {e}")
            # Fallback: just cycle
            self._navigate_by_index(1)

        # Hide cursor when using mouse
        self._cursor_visible = False
        self._show_popup()

    def _navigate_to_province(self, province_id: int) -> None:
        """Navigate to a specific province."""
        if province_id not in self._playable_provinces:
            return

        self._selected_province = province_id
        self._province_cycle_index = self._playable_provinces.index(province_id)

        # Get ruler for this province
        ruler_names = list(self.RULER_BIOS.keys())
        ruler_idx = (province_id - 1) % len(ruler_names)
        self._selected_ruler = ruler_names[ruler_idx]

        # Update cursor position to this province
        try:
            from UI.core.manager import UIManager

            manager = UIManager.get_instance()
            transform = manager.transform if manager else None
            self._update_cursor_position(province_id, transform)
        except:
            self._update_cursor_position(province_id)
        self._cursor_visible = True

        print(f"Navigated to province {province_id}: {self._selected_ruler}")

    def _get_province_center(self, province_id: int) -> tuple[float, float] | None:
        """Get the center point of a province from shape data."""
        shape = self.map_renderer.shape_manager.get_shape(province_id)
        if shape and shape.points:
            # Calculate centroid
            x_sum = sum(p[0] for p in shape.points)
            y_sum = sum(p[1] for p in shape.points)
            return (x_sum / len(shape.points), y_sum / len(shape.points))
        return None

    def _navigate_by_direction(self, direction: str) -> None:
        """Navigate to adjacent province in a direction.

        Args:
            direction: 'up', 'down', 'left', 'right'
        """
        if not self._selected_province:
            # First selection - start with province 1
            self._navigate_to_province(1)
            return

        # Get current province center
        current_center = self._get_province_center(self._selected_province)
        if not current_center:
            # Fallback to simple cycling
            delta = -1 if direction in ("up", "left") else 1
            self._navigate_by_index(delta)
            return

        # Get neighbors
        neighbors = self.map_renderer.shape_manager.get_neighbors(self._selected_province)
        if not neighbors:
            # No neighbors, try cycling through playable provinces
            delta = -1 if direction in ("up", "left") else 1
            self._navigate_by_index(delta)
            return

        # Find best neighbor in the requested direction
        best_neighbor = None
        best_score = float("-inf") if direction in ("down", "right") else float("inf")

        for neighbor_id in neighbors:
            neighbor_center = self._get_province_center(neighbor_id)
            if not neighbor_center:
                continue

            # Calculate relative position
            dx = neighbor_center[0] - current_center[0]
            dy = neighbor_center[1] - current_center[1]

            if direction == "up":
                # Want negative dy (above current)
                if dy < 0 and dy < best_score:
                    best_score = dy
                    best_neighbor = neighbor_id
            elif direction == "down":
                # Want positive dy (below current)
                if dy > 0 and dy > best_score:
                    best_score = dy
                    best_neighbor = neighbor_id
            elif direction == "left":
                # Want negative dx (left of current)
                if dx < 0 and dx < best_score:
                    best_score = dx
                    best_neighbor = neighbor_id
            elif direction == "right":
                # Want positive dx (right of current)
                if dx > 0 and dx > best_score:
                    best_score = dx
                    best_neighbor = neighbor_id

        if best_neighbor:
            self._navigate_to_province(best_neighbor)
        else:
            # No neighbor in that direction, cycle through playable provinces
            delta = -1 if direction in ("up", "left") else 1
            self._navigate_by_index(delta)

    def _navigate_by_index(self, delta: int) -> None:
        """Navigate by cycling through province list."""
        self._province_cycle_index = (self._province_cycle_index + delta) % len(
            self._playable_provinces
        )
        province_id = self._playable_provinces[self._province_cycle_index]
        self._navigate_to_province(province_id)

    def _toggle_nav_mode(self) -> None:
        """Toggle between adjacency and cursor navigation modes."""
        if self._nav_mode == self.NAV_MODE_ADJACENCY:
            self._nav_mode = self.NAV_MODE_CURSOR
            # Initialize free cursor at current province position
            if self._selected_province:
                self._update_cursor_position(self._selected_province)
                self._free_cursor_pos = self._cursor_pos
            print("Switched to CURSOR mode (free movement)")
        else:
            self._nav_mode = self.NAV_MODE_ADJACENCY
            # Find nearest province to cursor
            self._select_nearest_province_to_cursor()
            print("Switched to ADJACENCY mode (province jumping)")

    def _move_free_cursor(self, dx: float, dy: float) -> None:
        """Move free cursor in cursor mode."""
        x, y = self._free_cursor_pos
        x += dx
        y += dy

        # Keep within map bounds
        x = max(self._map_rect.left, min(self._map_rect.right, x))
        y = max(self._map_rect.top, min(self._map_rect.bottom, y))

        self._free_cursor_pos = (x, y)
        self._cursor_pos = (int(x), int(y))
        self._cursor_visible = True

        # Find province under cursor
        self._select_nearest_province_to_cursor()

    def _select_nearest_province_to_cursor(self) -> None:
        """Find and select the province nearest to the free cursor position."""
        try:
            from UI.core.manager import UIManager

            manager = UIManager.get_instance()
            if manager and manager.transform:
                # Get province at cursor position (like mouse click)
                province_id = self.map_renderer.get_province_at_screen_point(
                    (int(self._free_cursor_pos[0]), int(self._free_cursor_pos[1])),
                    manager.transform,
                )
                if province_id and province_id != self._selected_province:
                    self._selected_province = province_id
                    # Get ruler for this province
                    ruler_names = list(self.RULER_BIOS.keys())
                    ruler_idx = (province_id - 1) % len(ruler_names)
                    self._selected_ruler = ruler_names[ruler_idx]
                    print(f"Cursor at province {province_id}: {self._selected_ruler}")
        except Exception as e:
            print(f"Cursor selection error: {e}")

    def _select_province_at_cursor(self) -> None:
        """Show popup for province at cursor position (Enter in cursor mode)."""
        if self._selected_ruler:
            self._show_popup()
            self._focused_popup_button = 0
            self._update_popup_focus()

    def _update_cursor_position(self, province_id: int, transform=None) -> None:
        """Update cursor position to center of province using same coordinate system as mouse."""
        # Get province center in design coordinates
        center = self._get_province_center(province_id)
        if not center:
            # Fall back to province rect
            province_rect = self._get_province_rect(province_id)
            if province_rect:
                center = (province_rect.centerx, province_rect.centery)
            else:
                return

        # Convert design coordinates to screen coordinates using transform
        # This matches what get_province_at_screen_point does in reverse
        try:
            from UI.core.manager import UIManager

            manager = UIManager.get_instance()
            if manager and manager.transform:
                # Apply transform scaling and offset
                scale = manager.transform.get_scale()
                letterbox = manager.transform.get_letterbox_rect()
                map_offset_x, map_offset_y = self.map_renderer.DEFAULT_MAP_OFFSET

                # Calculate screen position (matching map_renderer.render)
                screen_x = int(letterbox.x + (map_offset_x + center[0]) * scale)
                # Add Y offset to align cursor with province number label
                # Province numbers appear ~50-60px below the centroid (in the lower part of province)
                screen_y = int(letterbox.y + (map_offset_y + center[1]) * scale) + 55

                self._cursor_pos = (screen_x, screen_y)
            else:
                # Fallback without transform
                map_x, map_y = self._map_offset
                self._cursor_pos = (
                    int(map_x + center[0]),
                    int(map_y + center[1]),
                )
        except Exception as e:
            # Fallback
            map_x, map_y = self._map_offset
            self._cursor_pos = (
                int(map_x + center[0]),
                int(map_y + center[1]),
            )

        self._cursor_target_province = province_id

    def _show_popup(self) -> None:
        """Show the ruler info popup."""
        if not self._selected_ruler:
            return

        self._showing_popup = True
        self._popup.visible = True

        # Update popup content
        self._popup_ruler_name.text = self._selected_ruler
        self._popup_province.text = f"Province {self._selected_province}"

        # Random stats for demo
        import random

        officers = random.randint(5, 20)
        soldiers = random.randint(10000, 80000)
        self._popup_stats.text = f"Officers: {officers}\nSoldiers: {soldiers:,}"

        # Bio
        bio = self.RULER_BIOS.get(self._selected_ruler, "No biography available.")
        self._popup_bio.text = bio

        # Load and display portrait
        self._update_portrait()

    def _update_portrait(self) -> None:
        """Load and display the ruler's portrait."""
        if not self._selected_ruler or not self._portrait_loader:
            return

        # Remove existing portrait image if any
        if self._portrait_image:
            if self._portrait_image in self._popup.children:
                self._popup.children.remove(self._portrait_image)
            self._portrait_image = None

        # Get officer ID for this ruler
        officer_id = self.RULER_OFFICER_IDS.get(self._selected_ruler, 0)

        # Load portrait
        portrait_size = (100, 100)
        portrait_surface = self._portrait_loader.get_portrait(officer_id, portrait_size)

        if portrait_surface:
            # Create UIImage with the portrait
            self._portrait_image = UIImage(
                image=portrait_surface,
                position=(25, 25),  # Slightly inside the portrait area
                size=portrait_size,
                parent=self._popup,
            )

    def _update_popup_focus(self) -> None:
        """Update visual focus on popup buttons."""
        if not self._popup_buttons:
            return

        # Clear focus from all buttons
        for btn in self._popup_buttons:
            btn.border_width = 0
            btn.border_color = None

        # Set focus on current button
        if 0 <= self._focused_popup_button < len(self._popup_buttons):
            focused_btn = self._popup_buttons[self._focused_popup_button]
            focused_btn.border_width = 3
            focused_btn.border_color = (255, 255, 255)

            # Also update UIManager focus for consistency
            try:
                from UI.core.manager import UIManager

                manager = UIManager.get_instance()
                if manager:
                    manager.set_focus(focused_btn)
            except:
                pass

    def _on_confirm_selection(self) -> None:
        """Confirm ruler selection."""
        if self._selected_ruler and self._callback:
            print(f"Confirmed ruler: {self._selected_ruler}")
            self._callback(self._selected_ruler)

    def _on_cancel_popup(self) -> None:
        """Cancel/hide popup."""
        self._showing_popup = False
        self._popup.visible = False

    def _on_random(self) -> None:
        """Select random ruler."""
        import random

        self._province_cycle_index = random.randint(0, len(self._playable_provinces) - 1)
        self._selected_province = self._playable_provinces[self._province_cycle_index]

        ruler_names = list(self.RULER_BIOS.keys())
        self._selected_ruler = ruler_names[self._province_cycle_index % len(ruler_names)]

        print(f"Random selection: {self._selected_ruler} (Province {self._selected_province})")
        self._show_popup()

    def _on_back(self) -> None:
        """Handle back button."""
        print("Back to scenario selection")
        if self._callback:
            self._callback(None)

    def set_callback(self, callback: Callable[[str | None], None]) -> None:
        """Set callback for ruler selection."""
        self._callback = callback

    def get_selected_ruler(self) -> str | None:
        """Get the selected ruler name."""
        return self._selected_ruler

    def render(self, surface: pygame.Surface, transform=None) -> None:
        """Render the screen."""
        # Clear background
        surface.fill(self.BG_COLOR)

        # Draw title and bottom buttons (excluding popup which handles itself)
        # Render non-popup, non-map children
        for child in self.children:
            if child != self._popup and child.visible:
                child.render(surface, transform)

        # Draw map area
        pygame.draw.rect(surface, (40, 40, 60), self._map_rect)
        pygame.draw.rect(surface, (79, 189, 186), self._map_rect, 2)

        # Draw map
        try:
            # Create temporary surface for map
            map_surf = pygame.Surface((self._map_rect.width, self._map_rect.height))
            if transform:
                self.map_renderer.render(map_surf, transform)
            else:
                # Simple render without transform
                pass
            surface.blit(map_surf, self._map_offset)
        except Exception as e:
            print(f"Map render error: {e}")

        # Draw keyboard/gamepad cursor (animated)
        if self._cursor_visible and self._cursor_target_province:
            self._draw_cursor(surface, self._cursor_pos)

        # Draw popup if visible (on top of everything)
        if self._showing_popup:
            # Darken background behind popup
            overlay = pygame.Surface((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(128)
            surface.blit(overlay, (0, 0))

            # Draw popup
            self._popup.render(surface, transform)

    def _get_province_rect(self, province_id: int) -> pygame.Rect | None:
        """Get approximate rect for a province on the map (for highlighting)."""
        # Simplified: return fixed positions for demo
        # In real implementation, this would come from province shape data
        # Positions are relative to the map surface (0,0 is top-left of map)
        positions = {
            1: (980, 80),
            2: (800, 80),
            3: (650, 80),
            4: (520, 100),
            5: (400, 150),
            6: (700, 140),
            7: (550, 200),
            8: (850, 200),
        }
        pos = positions.get(province_id, (500, 400))
        return pygame.Rect(pos[0], pos[1], 100, 80)

    def _draw_cursor(self, surface: pygame.Surface, pos: tuple[int, int]) -> None:
        """Draw an animated cursor at the given position."""
        import math
        import time

        # Cursor animation based on time
        t = time.time()
        pulse = abs(math.sin(t * 4))  # Pulsing effect
        size = 30 + int(pulse * 8)  # 30-38 pixels

        x, y = pos
        yellow = (255, 255, 100)
        orange = (255, 180, 50)

        # Draw outer glow (pulsing)
        glow_radius = size + 10
        glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        alpha = int(100 + pulse * 100)  # 100-200 alpha
        pygame.draw.circle(
            glow_surface, (255, 255, 100, alpha), (glow_radius, glow_radius), glow_radius
        )
        surface.blit(glow_surface, (x - glow_radius, y - glow_radius))

        # Draw crosshair lines
        pygame.draw.line(surface, yellow, (x - size, y), (x + size, y), 4)
        pygame.draw.line(surface, yellow, (x, y - size), (x, y + size), 4)

        # Draw corner brackets (larger)
        corner_size = size // 2
        bracket_width = 4

        # Top-left bracket
        pygame.draw.line(
            surface, orange, (x - size, y - size), (x - size + corner_size, y - size), bracket_width
        )
        pygame.draw.line(
            surface, orange, (x - size, y - size), (x - size, y - size + corner_size), bracket_width
        )
        # Top-right bracket
        pygame.draw.line(
            surface, orange, (x + size, y - size), (x + size - corner_size, y - size), bracket_width
        )
        pygame.draw.line(
            surface, orange, (x + size, y - size), (x + size, y - size + corner_size), bracket_width
        )
        # Bottom-left bracket
        pygame.draw.line(
            surface, orange, (x - size, y + size), (x - size + corner_size, y + size), bracket_width
        )
        pygame.draw.line(
            surface, orange, (x - size, y + size), (x - size, y + size - corner_size), bracket_width
        )
        # Bottom-right bracket
        pygame.draw.line(
            surface, orange, (x + size, y + size), (x + size - corner_size, y + size), bracket_width
        )
        pygame.draw.line(
            surface, orange, (x + size, y + size), (x + size, y + size - corner_size), bracket_width
        )

        # Draw center dot (pulsing)
        center_size = int(6 + pulse * 3)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), center_size)
        pygame.draw.circle(surface, yellow, (x, y), center_size - 2)

    def handle_event(self, event: pygame.event.Event, transform=None) -> bool:
        """Handle input events."""
        # If popup is showing, handle popup navigation first
        if self._showing_popup:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._on_cancel_popup()
                    return True
                elif event.key == pygame.K_LEFT:
                    # Move focus between popup buttons
                    self._focused_popup_button = max(0, self._focused_popup_button - 1)
                    self._update_popup_focus()
                    return True
                elif event.key == pygame.K_RIGHT:
                    # Move focus between popup buttons
                    self._focused_popup_button = min(1, self._focused_popup_button + 1)
                    self._update_popup_focus()
                    return True
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    # Activate focused popup button
                    if self._focused_popup_button == 0:
                        self._on_confirm_selection()
                    else:
                        self._on_cancel_popup()
                    return True

            # Let popup handle its own button clicks
            if self._popup.handle_event(event, transform):
                return True

            # Click outside popup closes it
            if event.type == pygame.MOUSEBUTTONDOWN:
                popup_rect = pygame.Rect(self._popup.position, self._popup.size)
                if not popup_rect.collidepoint(event.pos):
                    self._on_cancel_popup()
                    return True
            return False

        # Keyboard navigation for map (handle BEFORE passing to parent to avoid button focus)
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._on_back()
                return True
            elif event.key == pygame.K_TAB or event.key == pygame.K_s:
                # Toggle navigation mode (Tab or S key)
                self._toggle_nav_mode()
                return True
            elif self._nav_mode == self.NAV_MODE_CURSOR:
                # Free cursor movement mode (like mouse)
                if event.key == pygame.K_UP:
                    self._move_free_cursor(0, -self._free_cursor_speed)
                    return True
                elif event.key == pygame.K_DOWN:
                    self._move_free_cursor(0, self._free_cursor_speed)
                    return True
                elif event.key == pygame.K_LEFT:
                    self._move_free_cursor(-self._free_cursor_speed, 0)
                    return True
                elif event.key == pygame.K_RIGHT:
                    self._move_free_cursor(self._free_cursor_speed, 0)
                    return True
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Select province under cursor
                    self._select_province_at_cursor()
                    return True
                elif event.key == pygame.K_r:
                    self._on_random()
                    return True
            else:
                # Adjacency navigation mode (jump between provinces)
                if event.key == pygame.K_UP:
                    self._navigate_by_direction("up")
                    return True
                elif event.key == pygame.K_DOWN:
                    self._navigate_by_direction("down")
                    return True
                elif event.key == pygame.K_LEFT:
                    self._navigate_by_direction("left")
                    return True
                elif event.key == pygame.K_RIGHT:
                    self._navigate_by_direction("right")
                    return True
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    # Show popup on enter/space and set focus to Select button
                    self._show_popup()
                    self._focused_popup_button = 0  # Start with Select button focused
                    self._update_popup_focus()
                    return True
                elif event.key == pygame.K_r:
                    self._on_random()
                    return True

            # Track key presses for repeat handling (cursor mode only)
            if self._nav_mode == self.NAV_MODE_CURSOR and event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    self._key_states[event.key] = True
                    self._key_press_times[event.key] = 0  # Will be set in update
                    self._key_last_repeat[event.key] = 0

        # Track key releases
        if event.type == pygame.KEYUP:
            if event.key in self._key_states:
                del self._key_states[event.key]
                if event.key in self._key_press_times:
                    del self._key_press_times[event.key]
                if event.key in self._key_last_repeat:
                    del self._key_last_repeat[event.key]

        # Check for map click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._map_rect.collidepoint(event.pos):
                self._on_map_click(event.pos[0], event.pos[1], transform)
                return True

        # Pass to parent for button clicks only (keyboard already handled above)
        if super().handle_event(event, transform):
            return True

        return False

    def update(self, dt: float) -> None:
        """Update screen - handle key repeats for cursor mode."""
        super().update(dt)

        # Handle key repeats in cursor mode
        if self._nav_mode == self.NAV_MODE_CURSOR and self._key_states:
            import time

            current_time = time.time()

            for key in self._key_states:
                # Initialize press time if not set
                if key not in self._key_press_times or self._key_press_times[key] == 0:
                    self._key_press_times[key] = current_time
                    self._key_last_repeat[key] = current_time
                    continue

                press_time = self._key_press_times[key]
                last_repeat = self._key_last_repeat[key]

                # Check if we should repeat
                elapsed = current_time - press_time
                since_last = current_time - last_repeat

                # First repeat after delay, then regular interval
                if elapsed > self._key_repeat_delay and since_last > self._key_repeat_interval:
                    # Repeat the key action
                    if key == pygame.K_UP:
                        self._move_free_cursor(0, -self._free_cursor_speed)
                    elif key == pygame.K_DOWN:
                        self._move_free_cursor(0, self._free_cursor_speed)
                    elif key == pygame.K_LEFT:
                        self._move_free_cursor(-self._free_cursor_speed, 0)
                    elif key == pygame.K_RIGHT:
                        self._move_free_cursor(self._free_cursor_speed, 0)

                    self._key_last_repeat[key] = current_time


def test_ruler_selection():
    """Test the ruler selection screen."""
    pygame.init()

    screen = pygame.display.set_mode((1280, 800))
    pygame.display.set_caption("ROTK2 - Ruler Selection Test")

    clock = pygame.time.Clock()

    # Create UIManager
    manager = UIManager.get_instance()
    manager.actual_resolution = (1280, 800)
    from UI.core.transform import Transform

    manager.transform = Transform((1280, 800), (1280, 800))

    # Create screen
    screen_obj = RulerSelectionScreen()
    manager.root_component = screen_obj
    manager.current_screen = screen_obj

    selected_ruler = None

    def on_select(ruler: str | None):
        nonlocal selected_ruler
        selected_ruler = ruler
        if ruler:
            print(f"\n>>> Ruler selected: {ruler}")
        else:
            print("\n>>> Back to scenario selection")

    screen_obj.set_callback(on_select)

    print("\n" + "=" * 50)
    print("Ruler Selection Test")
    print("=" * 50)
    print("Controls:")
    print("  Click on map - Select/cycle province")
    print("  Arrow keys - Navigate provinces")
    print("  Enter/Space - Show ruler info popup")
    print("  R - Random ruler")
    print("  ESC - Back")
    print("=" * 50)

    running = True
    frame_count = 0
    while running:
        dt = clock.tick(60) / 1000.0
        frame_count += 1

        # Process events
        try:
            events = pygame.event.get()
        except (SystemError, KeyError) as e:
            print(f"Warning: Event hiccup (frame {frame_count}): {e}")
            events = []

        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and pygame.key.get_mods() & pygame.KMOD_CTRL:
                    running = False

            try:
                manager.handle_event(event)
            except Exception as e:
                print(f"Event error (non-fatal): {e}")

        if selected_ruler is not None:
            running = False

        # Update and render
        try:
            manager.update(dt)
        except Exception as e:
            print(f"Update error (non-fatal): {e}")

        try:
            screen.fill((15, 15, 25))
            manager.render(screen)
            pygame.display.flip()
        except Exception as e:
            print(f"Render error: {e}")
            running = False

    pygame.quit()
    print("\nTest complete!")


if __name__ == "__main__":
    test_ruler_selection()
