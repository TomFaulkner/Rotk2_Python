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

    def __init__(self, screen: pygame.Surface, hex_size: int = 24):
        """
        Initialize battle renderer.

        Args:
            screen: Pygame surface to render to
            hex_size: Size of hexes in pixels (radius)
        """
        self.screen = screen
        self.hex_size = hex_size
        self.hex_width = hex_size * 2
        self.hex_height = int(hex_size * 1.732)  # sqrt(3)

        # Fonts
        self.font = pygame.font.SysFont(None, 20)
        self.small_font = pygame.font.SysFont(None, 16)

        # View offset for scrolling
        self.offset_x = 50
        self.offset_y = 50

        # Cache for hex polygons
        self._hex_cache: Dict[Tuple[int, int], List[Tuple[int, int]]] = {}

        # Load portrait mapping
        self.portrait_mapping = self._load_portrait_mapping()
        self.portrait_cache: Dict[str, pygame.Surface] = {}

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

    def hex_to_pixel(self, coord: HexCoord) -> Tuple[int, int]:
        """
        Convert hex coordinate to pixel position.

        Args:
            coord: Hex coordinate

        Returns:
            (x, y) pixel position
        """
        col = coord.col
        row = coord.row

        # Staggered grid: odd columns are offset
        x = col * (self.hex_width * 0.75)
        y = row * self.hex_height

        if col % 2 == 1:
            y += self.hex_height / 2

        return int(x + self.offset_x), int(y + self.offset_y)

    def get_hex_polygon(self, coord: HexCoord) -> List[Tuple[int, int]]:
        """
        Get the polygon points for a hex.

        Args:
            coord: Hex coordinate

        Returns:
            List of (x, y) points
        """
        cache_key = (coord.row, coord.col)
        if cache_key in self._hex_cache:
            return self._hex_cache[cache_key]

        cx, cy = self.hex_to_pixel(coord)

        points = []
        for i in range(6):
            angle_deg = 60 * i - 30
            angle_rad = 3.14159 / 180 * angle_deg
            x = (
                cx
                + self.hex_size
                * 0.9
                * pygame.math.Vector2(pygame.math.Vector2(1, 0).rotate(angle_deg)).x
            )
            y = (
                cy
                + self.hex_size
                * 0.9
                * pygame.math.Vector2(pygame.math.Vector2(1, 0).rotate(angle_deg)).y
            )

            # Manual calculation for reliability
            import math

            x = cx + self.hex_size * 0.9 * math.cos(angle_rad)
            y = cy + self.hex_size * 0.9 * math.sin(angle_rad)
            points.append((int(x), int(y)))

        self._hex_cache[cache_key] = points
        return points

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
        Render the hex grid.

        Args:
            grid: HexGrid to render
            highlight_hexes: Optional list of hexes to highlight
        """
        highlight_set = set(highlight_hexes) if highlight_hexes else set()

        for coord, hex_obj in grid.hexes.items():
            points = self.get_hex_polygon(coord)

            # Get terrain color
            color = self.get_terrain_color(hex_obj.terrain)

            # Highlight if needed
            if coord in highlight_set:
                # Blend with highlight color
                color = (
                    min(255, color[0] + 50),
                    min(255, color[1] + 50),
                    min(255, color[2] + 50),
                )

            # Draw hex
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.polygon(self.screen, self.COLORS["grid_line"], points, 1)

            # Draw castle symbol if castle
            if hex_obj.terrain == TerrainType.CASTLE or hex_obj.is_castle:
                cx, cy = self.hex_to_pixel(coord)
                pygame.draw.rect(self.screen, (0, 0, 0), (cx - 5, cy - 5, 10, 10))

            # Draw fire if burning
            if hex_obj.is_burning:
                cx, cy = self.hex_to_pixel(coord)
                # Draw flame effect (orange circle with red center)
                pygame.draw.circle(self.screen, self.COLORS["burning"], (cx, cy), 8)
                pygame.draw.circle(self.screen, (255, 0, 0), (cx, cy), 4)
                # Draw small flame tips
                for angle in [0.2, 1.0, 1.8, 2.6]:
                    import math

                    fx = cx + int(8 * math.cos(angle))
                    fy = cy - int(8 * math.sin(angle))
                    pygame.draw.circle(self.screen, (255, 100, 0), (fx, fy), 3)

    def render_unit(self, unit: BattleUnit, selected: bool = False):
        """
        Render a unit on the grid.

        Args:
            unit: BattleUnit to render
            selected: True if this unit is selected
        """
        if not unit.position:
            return

        cx, cy = self.hex_to_pixel(unit.position)

        # Determine color based on side and state
        if unit.is_attacker:
            color = (255, 100, 100) if not selected else (255, 200, 100)
        else:
            color = (100, 100, 255) if not selected else (100, 200, 255)

        if unit.is_defeated():
            color = (64, 64, 64)

        # Draw unit circle
        pygame.draw.circle(self.screen, color, (cx, cy), self.hex_size // 2 - 2)
        pygame.draw.circle(self.screen, (0, 0, 0), (cx, cy), self.hex_size // 2 - 2, 2)

        # Draw soldier count
        soldiers_text = str(unit.soldiers)
        text_surface = self.small_font.render(soldiers_text, True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(cx, cy))
        self.screen.blit(text_surface, text_rect)

        # Draw commander star
        if unit.is_commander:
            pygame.draw.polygon(
                self.screen,
                (255, 215, 0),
                [
                    (cx, cy - 12),
                    (cx + 3, cy - 6),
                    (cx + 9, cy - 6),
                    (cx + 4, cy - 2),
                    (cx + 6, cy + 4),
                    (cx, cy + 1),
                    (cx - 6, cy + 4),
                    (cx - 4, cy - 2),
                    (cx - 9, cy - 6),
                    (cx - 3, cy - 6),
                ],
            )

    def render_units(
        self, units: List[BattleUnit], selected_unit: Optional[BattleUnit] = None
    ):
        """
        Render all units.

        Args:
            units: List of BattleUnits to render
            selected_unit: Currently selected unit
        """
        for unit in units:
            is_selected = unit == selected_unit
            self.render_unit(unit, is_selected)

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
        points = self.get_hex_polygon(start)
        pygame.draw.polygon(self.screen, self.COLORS["selected"], points, 3)

        # Highlight reachable hexes
        for coord in reachable_hexes:
            points = self.get_hex_polygon(coord)
            pygame.draw.polygon(self.screen, self.COLORS["movable"], points, 2)

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

    def get_hex_at_pixel(
        self, grid: HexGrid, pixel_x: int, pixel_y: int
    ) -> Optional[HexCoord]:
        """
        Find hex coordinate at pixel position.

        Args:
            grid: HexGrid
            pixel_x: X pixel coordinate
            pixel_y: Y pixel coordinate

        Returns:
            HexCoord or None
        """
        # Simple distance check to all hex centers
        for coord in grid.hexes.keys():
            hx, hy = self.hex_to_pixel(coord)
            dist = ((pixel_x - hx) ** 2 + (pixel_y - hy) ** 2) ** 0.5
            if dist < self.hex_size:
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

        # Render units
        self.render_units(units, selected_unit)

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

    renderer = BattleRenderer(screen, hex_size=24)

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
