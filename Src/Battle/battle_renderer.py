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

    def render_selected_unit_info(
        self, unit: Optional[BattleUnit], x: int = 10, y: int = 10
    ):
        """
        Render info for selected unit.

        Args:
            unit: Selected BattleUnit
            x: X position
            y: Y position
        """
        if not unit:
            return

        # Draw panel
        panel_width = 180
        panel_height = 120
        pygame.draw.rect(self.screen, (32, 32, 32), (x, y, panel_width, panel_height))
        pygame.draw.rect(
            self.screen, (100, 100, 100), (x, y, panel_width, panel_height), 2
        )

        # Unit info
        y_offset = y + 5

        name_text = unit.get_officer_name()
        surface = self.font.render(name_text, True, self.COLORS["text"])
        self.screen.blit(surface, (x + 5, y_offset))
        y_offset += 22

        stats = [
            f"Soldiers: {unit.soldiers}",
            f"War: {unit.get_war_ability()}",
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

        # Render UI
        if battle_engine:
            self.render_ui(battle_engine)

        # Render selected unit info
        self.render_selected_unit_info(selected_unit)


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
