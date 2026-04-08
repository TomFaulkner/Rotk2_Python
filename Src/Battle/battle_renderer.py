"""
Battle renderer for visual display.

Handles rendering the battle hex grid, units, and UI elements.
"""

import pygame
from typing import List, Optional, Tuple, Dict, Any
from pathlib import Path

from .hex_grid import HexGrid, HexCoord, TerrainType
from .battle_unit import BattleUnit


class BattleRenderer:
    """
    Renders the battle screen.

    Displays:
    - Hex grid with terrain
    - Units with portraits
    - Movement ranges
    - UI elements
    """

    # Colors
    COLORS = {
        "background": (0, 0, 0),
        "plains": (139, 90, 43),  # Brown
        "forest": (34, 85, 51),  # Dark green
        "hills": (101, 67, 33),  # Dark brown
        "water": (65, 105, 225),  # Royal blue
        "castle": (128, 128, 128),  # Gray
        "mountain": (64, 64, 64),  # Dark gray
        "burning": (255, 69, 0),  # Orange-red for fire
        "grid_line": (100, 100, 100),
        "highlight": (255, 255, 0, 128),
        "selected": (0, 255, 0, 128),
        "enemy": (255, 0, 0, 128),
        "movable": (0, 255, 255, 128),
        "text": (255, 255, 255),
    }

    def __init__(self, screen: pygame.Surface, tile_size: int = 32):
        """
        Initialize battle renderer.

        Args:
            screen: Pygame surface to render to
            tile_size: Size of tiles in pixels (default 32 for original ROTK2)
        """
        self.screen = screen
        self.tile_size = tile_size
        self.tile_width = tile_size
        self.tile_height = tile_size
        self.stagger_offset = tile_size // 2  # 50% offset for odd columns

        # Fonts
        self.font = pygame.font.SysFont(None, 20)
        self.small_font = pygame.font.SysFont(None, 16)

        # View offset for scrolling
        self.offset_x = 50
        self.offset_y = 50

        # Load portrait mapping
        self.portrait_mapping = self._load_portrait_mapping()
        self.portrait_cache: Dict[str, pygame.Surface] = {}

        # Load terrain images
        self.terrain_images = self._load_terrain_images()

        # Terrain type to image index mapping
        # Note: Image indices match the original game terrain codes, not our TerrainType enum
        self.terrain_image_map = {
            TerrainType.PLAINS: 0,  # hex00.jpg (code 0)
            TerrainType.FOREST: 1,  # hex01.jpg (code 1)
            TerrainType.HILLS: 2,  # hex02.jpg (code 2)
            TerrainType.MOUNTAIN: 3,  # hex03.jpg (code 3) - mountain
            TerrainType.WATER: 4,  # hex04.jpg (code 4) - water
            TerrainType.CASTLE: 5,  # hex05.jpg (code 5) - fort/mini-castle
            # Code 6 (main castle) also uses CASTLE type but is marked with is_castle flag
        }

    def _load_portrait_mapping(self) -> Dict:
        """Load officer ID to portrait file mapping."""
        import json

        try:
            # Try multiple possible paths for the mapping file
            possible_paths = [
                Path("Resources/portraits/portrait_mapping.json"),  # From project root
                Path("../Resources/portraits/portrait_mapping.json"),  # From Src/
            ]

            for mapping_path in possible_paths:
                if mapping_path.exists():
                    with open(mapping_path, "r") as f:
                        return json.load(f)
        except Exception as e:
            print(f"Failed to load portrait mapping: {e}")
        return {}

    def _load_terrain_images(self) -> Dict[int, pygame.Surface]:
        """Load terrain hex images."""
        images = {}
        try:
            # Try multiple possible paths for terrain images
            possible_paths = [
                Path("Resources"),  # From project root
                Path("../Resources"),  # From Src/
            ]

            for base_path in possible_paths:
                if base_path.exists():
                    # Load all hex images (hex00.jpg through hex06.jpg, hex09.jpg, hex99.jpg)
                    for i in range(0, 10):  # 0-9
                        img_path = base_path / f"hex{i:02d}.jpg"
                        if img_path.exists():
                            img = pygame.image.load(str(img_path))
                            images[i] = img
                    # Also load special hex types
                    for special in [99]:
                        img_path = base_path / f"hex{special:02d}.jpg"
                        if img_path.exists():
                            img = pygame.image.load(str(img_path))
                            images[special] = img
                    break
        except Exception as e:
            print(f"Failed to load terrain images: {e}")
        return images

    def _get_officer_portrait(self, officer_id: int) -> Optional[pygame.Surface]:
        """Load officer portrait by ID."""
        if str(officer_id) not in self.portrait_mapping:
            return None

        mapping = self.portrait_mapping[str(officer_id)]
        file_path = mapping.get("file", "")

        # Check cache first
        if file_path in self.portrait_cache:
            return self.portrait_cache[file_path]

        # Load portrait - handle relative paths from different working directories
        try:
            # Try the path as-is first (relative to current directory)
            full_path = Path(file_path)
            if not full_path.exists():
                # Try from project root (remove ../ prefix if present)
                if file_path.startswith("../"):
                    full_path = Path(file_path[3:])  # Remove ../
                else:
                    full_path = Path("Resources/portraits/") / file_path

            if full_path.exists():
                portrait = pygame.image.load(str(full_path))
                # Scale to fit panel (80x100)
                portrait = pygame.transform.scale(portrait, (80, 100))
                self.portrait_cache[file_path] = portrait
                return portrait
        except Exception:
            pass
        return None

    def coord_to_pixel(self, coord: HexCoord) -> Tuple[int, int]:
        """
        Convert grid coordinate to pixel position (staggered square tiles).

        Args:
            coord: Grid coordinate

        Returns:
            (x, y) pixel position
        """
        col = coord.col
        row = coord.row

        # Staggered square grid: odd columns are offset by 50%
        x = col * self.tile_width
        y = row * self.tile_height + (col % 2) * self.stagger_offset

        return int(x + self.offset_x), int(y + self.offset_y)

    def get_tile_rect(self, coord: HexCoord) -> Tuple[int, int, int, int]:
        """
        Get the rectangle for a tile.

        Args:
            coord: Grid coordinate

        Returns:
            (x, y, width, height) rectangle
        """
        x, y = self.coord_to_pixel(coord)
        return (x, y, self.tile_width, self.tile_height)

    def get_terrain_color(self, terrain: TerrainType) -> Tuple[int, int, int]:
        """
        Get color for terrain type.

        Args:
            terrain: Terrain type

        Returns:
            RGB color tuple
        """
        color_map = {
            TerrainType.PLAINS: self.COLORS["plains"],
            TerrainType.FOREST: self.COLORS["forest"],
            TerrainType.HILLS: self.COLORS["hills"],
            TerrainType.WATER: self.COLORS["water"],
            TerrainType.CASTLE: self.COLORS["castle"],
            TerrainType.MOUNTAIN: self.COLORS["mountain"],
        }
        return color_map.get(terrain, self.COLORS["plains"])

    def render_grid(
        self, grid: HexGrid, highlight_hexes: Optional[List[HexCoord]] = None
    ):
        """
        Render the grid using terrain images (staggered square tiles).

        Args:
            grid: HexGrid to render
            highlight_hexes: Optional list of hexes to highlight
        """
        highlight_set = set(highlight_hexes) if highlight_hexes else set()

        for coord, hex_obj in grid.hexes.items():
            x, y = self.coord_to_pixel(coord)

            # Get terrain image
            img_idx = self.terrain_image_map.get(hex_obj.terrain, 0)
            terrain_img = self.terrain_images.get(img_idx)

            if terrain_img:
                # Blit terrain image
                self.screen.blit(terrain_img, (x, y))
            else:
                # Fallback to colored rectangle
                color = self.get_terrain_color(hex_obj.terrain)
                pygame.draw.rect(
                    self.screen, color, (x, y, self.tile_width, self.tile_height)
                )

            # Highlight if needed
            if coord in highlight_set:
                # Draw semi-transparent highlight overlay
                highlight_surface = pygame.Surface((self.tile_width, self.tile_height))
                highlight_surface.set_alpha(100)
                highlight_surface.fill((255, 255, 0))
                self.screen.blit(highlight_surface, (x, y))

            # Draw fire if burning
            if hex_obj.is_burning:
                cx, cy = x + self.tile_width // 2, y + self.tile_height // 2
                # Draw flame effect (orange circle with red center)
                pygame.draw.circle(self.screen, self.COLORS["burning"], (cx, cy), 8)
                pygame.draw.circle(self.screen, (255, 0, 0), (cx, cy), 4)
                # Draw small flame tips
                for angle in [0.2, 1.0, 1.8, 2.6]:
                    import math

                    fx = cx + int(8 * math.cos(angle))
                    fy = cy - int(8 * math.sin(angle))
                    pygame.draw.circle(self.screen, (255, 100, 0), (fx, fy), 3)

    def render_unit(
        self,
        unit: BattleUnit,
        selected: bool = False,
        viewer_is_attacker: Optional[bool] = None,
    ):
        """
        Render a unit on the grid.

        Args:
            unit: BattleUnit to render
            selected: True if this unit is selected
            viewer_is_attacker: Side of the player viewing the unit (for hidden unit visibility)
        """
        if not unit.position:
            return

        # Check if unit is hidden
        if unit.is_hidden():
            # Hidden units are invisible to enemies
            if (
                viewer_is_attacker is not None
                and unit.is_attacker != viewer_is_attacker
            ):
                return  # Don't render enemy hidden units
            # Owner sees hidden units semi-transparent
            is_hidden_visible = True
        else:
            is_hidden_visible = False

        x, y = self.coord_to_pixel(unit.position)
        cx = x + self.tile_width // 2
        cy = y + self.tile_height // 2

        # Determine color based on side and state
        if unit.is_attacker:
            color = (255, 100, 100) if not selected else (255, 200, 100)
        else:
            color = (100, 100, 255) if not selected else (100, 200, 255)

        if unit.is_defeated():
            color = (64, 64, 64)

        # For hidden units, make semi-transparent
        if is_hidden_visible:
            # Create semi-transparent surface for the unit
            unit_surface = pygame.Surface(
                (self.tile_width, self.tile_height), pygame.SRCALPHA
            )
            # Draw unit circle on the surface with transparency
            pygame.draw.circle(
                unit_surface,
                (*color, 128),
                (self.tile_width // 2, self.tile_height // 2),
                self.tile_width // 3,
            )
            pygame.draw.circle(
                unit_surface,
                (0, 0, 0, 128),
                (self.tile_width // 2, self.tile_height // 2),
                self.tile_width // 3,
                2,
            )
            self.screen.blit(unit_surface, (x, y))
        else:
            # Draw unit circle normally
            radius = self.tile_width // 3
            pygame.draw.circle(self.screen, color, (cx, cy), radius)
            pygame.draw.circle(self.screen, (0, 0, 0), (cx, cy), radius, 2)

        # Draw soldier count
        soldiers_text = str(unit.soldiers)
        text_surface = self.small_font.render(soldiers_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(cx, cy))
        self.screen.blit(text_surface, text_rect)

        # Draw commander star
        if unit.is_commander:
            star_size = 10
            pygame.draw.polygon(
                self.screen,
                (255, 215, 0),
                [
                    (cx, cy - star_size),
                    (cx + 3, cy - star_size // 2),
                    (cx + 9, cy - star_size // 2),
                    (cx + 4, cy - 2),
                    (cx + 6, cy + 4),
                    (cx, cy + 1),
                    (cx - 6, cy + 4),
                    (cx - 4, cy - 2),
                    (cx - 9, cy - star_size // 2),
                    (cx - 3, cy - star_size // 2),
                ],
            )

    def render_units(
        self,
        units: List[BattleUnit],
        selected_unit: Optional[BattleUnit] = None,
        viewer_is_attacker: Optional[bool] = None,
    ):
        """
        Render all units.

        Args:
            units: List of BattleUnits to render
            selected_unit: Currently selected unit
            viewer_is_attacker: Side of the player viewing (for hidden unit visibility)
        """
        for unit in units:
            is_selected = unit == selected_unit
            self.render_unit(unit, is_selected, viewer_is_attacker)

    def render_movement_range(
        self,
        grid: HexGrid,
        start: HexCoord,
        mobility: int,
        reachable_hexes: List[HexCoord],
    ):
        """
        Render movement range highlights.

        Args:
            grid: HexGrid
            start: Starting position
            mobility: Mobility points
            reachable_hexes: List of reachable coordinates
        """
        # Highlight start position
        x, y = self.coord_to_pixel(start)
        pygame.draw.rect(
            self.screen,
            self.COLORS["selected"],
            (x, y, self.tile_width, self.tile_height),
            3,
        )

        # Highlight reachable hexes
        for coord in reachable_hexes:
            x, y = self.coord_to_pixel(coord)
            pygame.draw.rect(
                self.screen,
                self.COLORS["movable"],
                (x, y, self.tile_width, self.tile_height),
                2,
            )

    def render_ui(self, battle_engine: Any):
        """
        Render UI elements.

        Args:
            battle_engine: BattleEngine with battle info
        """
        # Battle info panel (right side)
        panel_x = self.screen.get_width() - 200
        panel_y = 10

        # Draw panel background
        pygame.draw.rect(
            self.screen, (32, 32, 32), (panel_x - 10, panel_y - 10, 190, 400)
        )
        pygame.draw.rect(
            self.screen, (100, 100, 100), (panel_x - 10, panel_y - 10, 190, 400), 2
        )

        # Battle info
        y = panel_y

        # Day/Turn
        day_text = f"Day: {battle_engine.day}"
        surface = self.font.render(day_text, True, self.COLORS["text"])
        self.screen.blit(surface, (panel_x, y))
        y += 25

        # Current turn
        turn_text = f"Turn: {'Attacker' if battle_engine.turn == 0 else 'Defender'}"
        surface = self.font.render(turn_text, True, self.COLORS["text"])
        self.screen.blit(surface, (panel_x, y))
        y += 35

        # Unit counts
        attacker_count = len(battle_engine.get_attacking_units_on_map())
        defender_count = len(battle_engine.get_defending_units_on_map())

        atk_text = f"Attackers: {attacker_count}"
        surface = self.font.render(atk_text, True, (255, 150, 150))
        self.screen.blit(surface, (panel_x, y))
        y += 25

        def_text = f"Defenders: {defender_count}"
        surface = self.font.render(def_text, True, (150, 150, 255))
        self.screen.blit(surface, (panel_x, y))
        y += 35

        # Reserve counts
        atk_res_text = f"A Reserve: {len(battle_engine.attacker_reserve)}"
        surface = self.small_font.render(atk_res_text, True, (200, 200, 200))
        self.screen.blit(surface, (panel_x, y))
        y += 20

        def_res_text = f"D Reserve: {len(battle_engine.defender_reserve)}"
        surface = self.small_font.render(def_res_text, True, (200, 200, 200))
        self.screen.blit(surface, (panel_x, y))
        y += 35

        # Rice supplies
        att_rice = battle_engine.attacker_supplies.get("rice", 0)
        def_rice = battle_engine.defender_supplies.get("rice", 0)

        rice_color = (
            (255, 255, 200)
            if att_rice > 20
            else (255, 200, 100)
            if att_rice > 0
            else (255, 100, 100)
        )
        att_rice_text = f"A Rice: {att_rice}"
        surface = self.small_font.render(att_rice_text, True, rice_color)
        self.screen.blit(surface, (panel_x, y))
        y += 20

        rice_color = (
            (255, 255, 200)
            if def_rice > 20
            else (255, 200, 100)
            if def_rice > 0
            else (255, 100, 100)
        )
        def_rice_text = f"D Rice: {def_rice}"
        surface = self.small_font.render(def_rice_text, True, rice_color)
        self.screen.blit(surface, (panel_x, y))

    def render_selected_unit_info(
        self, unit: Optional[BattleUnit], x: int = 10, y: int = 10
    ):
        """
        Render info for selected unit with portrait.

        Args:
            unit: Selected BattleUnit
            x: X position
            y: Y position
        """
        if not unit:
            return

        # Draw panel (taller to fit portrait and all stats)
        panel_width = 200
        panel_height = 220
        pygame.draw.rect(self.screen, (32, 32, 32), (x, y, panel_width, panel_height))
        pygame.draw.rect(
            self.screen, (100, 100, 100), (x, y, panel_width, panel_height), 2
        )

        # Get officer ID for portrait
        officer_id = getattr(unit.officer, "Id", None)

        # Load and display portrait
        portrait = None
        if officer_id is not None:
            portrait = self._get_officer_portrait(officer_id)

        if portrait:
            # Portrait on the left side
            portrait_x = x + 5
            portrait_y = y + 5
            self.screen.blit(portrait, (portrait_x, portrait_y))

            # Name above stats
            name_text = unit.get_officer_name()
            surface = self.font.render(name_text, True, self.COLORS["text"])
            self.screen.blit(surface, (portrait_x, portrait_y + 105))

            # Stats on the right of portrait
            y_offset = portrait_y
            stats = [
                f"Sold: {unit.soldiers}",
                f"War: {unit.get_war_ability()}",
                f"Int: {unit.get_intelligence()}",
                f"Mob: {unit.mobility}/{unit.MAX_MOBILITY}",
                f"Trn: {unit.training}",
                f"Loy: {unit.loyalty}",
            ]
            stats_x = x + 90  # Right of portrait
            for stat in stats:
                surface = self.small_font.render(stat, True, (200, 200, 200))
                self.screen.blit(surface, (stats_x, y_offset))
                y_offset += 17
        else:
            # No portrait - text layout
            y_offset = y + 5

            name_text = unit.get_officer_name()
            surface = self.font.render(name_text, True, self.COLORS["text"])
            self.screen.blit(surface, (x + 5, y_offset))
            y_offset += 22

            stats = [
                f"Soldiers: {unit.soldiers}",
                f"War: {unit.get_war_ability()}",
                f"Int: {unit.get_intelligence()}",
                f"Mobility: {unit.mobility}/{unit.MAX_MOBILITY}",
                f"Training: {unit.training}",
                f"Loyalty: {unit.loyalty}",
            ]

            for stat in stats:
                surface = self.small_font.render(stat, True, (200, 200, 200))
                self.screen.blit(surface, (x + 5, y_offset))
                y_offset += 18

    def get_tile_at_pixel(
        self, grid: HexGrid, pixel_x: int, pixel_y: int
    ) -> Optional[HexCoord]:
        """
        Find tile coordinate at pixel position (for staggered square grid).

        Args:
            grid: HexGrid
            pixel_x: X pixel coordinate
            pixel_y: Y pixel coordinate

        Returns:
            HexCoord or None
        """
        # Adjust for offset
        adj_x = pixel_x - self.offset_x
        adj_y = pixel_y - self.offset_y

        # Calculate column
        col = int(adj_x // self.tile_width)
        if col < 0 or col >= 13:  # 13 columns
            return None

        # Check if column is valid
        if col not in range(13):
            return None

        # Calculate row accounting for stagger
        stagger = (col % 2) * self.stagger_offset
        row = int((adj_y - stagger) // self.tile_height)

        # Verify the coordinate is within bounds
        if row < 0 or row >= 12:  # 12 rows
            return None

        # Create coord and verify it exists in grid
        coord = HexCoord(row, col)
        if coord in grid.hexes:
            return coord

        return None

    def clear_screen(self):
        """Clear the screen."""
        self.screen.fill(self.COLORS["background"])

    def render(
        self,
        grid: HexGrid,
        units: List[BattleUnit],
        selected_unit: Optional[BattleUnit] = None,
        reachable_hexes: Optional[List[HexCoord]] = None,
        battle_engine: Any = None,
    ):
        """
        Render complete battle scene.

        Args:
            grid: HexGrid
            units: All units to render
            selected_unit: Currently selected unit
            reachable_hexes: Movement range highlights
            battle_engine: Battle engine for UI
        """
        self.clear_screen()

        # Render grid
        self.render_grid(grid)

        # Render movement range if applicable
        if selected_unit and reachable_hexes and selected_unit.position:
            self.render_movement_range(
                grid, selected_unit.position, selected_unit.mobility, reachable_hexes
            )

        # Render units (pass viewer side for hidden unit visibility)
        # In hotseat 2-player mode, viewer is determined by whose turn it is
        viewer_is_attacker = battle_engine.turn == 0 if battle_engine else None
        self.render_units(units, selected_unit, viewer_is_attacker)

        # Render selected unit info at top right (replacing the old battle info panel)
        panel_width = 200  # Updated to match render_selected_unit_info
        panel_height = 220  # Updated to fit portrait and all stats
        panel_x = self.screen.get_width() - panel_width - 10  # Right side
        panel_y = 10  # Top
        self.render_selected_unit_info(selected_unit, x=panel_x, y=panel_y)


if __name__ == "__main__":
    # Test renderer
    print("Testing BattleRenderer...")

    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Battle Renderer Test")

    renderer = BattleRenderer(screen, tile_size=32)

    # Create grid
    grid = HexGrid()

    # Test render
    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        renderer.clear_screen()
        renderer.render_grid(grid)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    print("BattleRenderer test complete!")
