"""
Hex grid system for battle maps.

Implements a 12x13 staggered hex grid for ROTK2 battles.
"""

import json
import random
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from enum import Enum


class TerrainType(Enum):
    """Terrain types for hexes."""

    PLAINS = 0
    FOREST = 1
    HILLS = 2
    WATER = 3
    CASTLE = 4
    MOUNTAIN = 5  # Impassable
    EMPTY = 99


class HexCoord:
    """Represents a coordinate on the hex grid."""

    def __init__(self, row: int, col: int):
        """
        Initialize hex coordinate.

        Args:
            row: Row index (0-11)
            col: Column index (0-12)
        """
        self.row = row
        self.col = col

    def __eq__(self, other: object) -> bool:
        """Check equality with another HexCoord."""
        if not isinstance(other, HexCoord):
            return False
        return self.row == other.row and self.col == other.col

    def __hash__(self) -> int:
        """Hash for use in dictionaries."""
        return hash((self.row, self.col))

    def __repr__(self) -> str:
        """String representation."""
        return f"HexCoord({self.row}, {self.col})"

    def __str__(self) -> str:
        """Human readable string."""
        return f"({self.row}, {self.col})"

    def is_valid(self, max_rows: int = 12, max_cols: int = 13) -> bool:
        """
        Check if coordinate is within grid bounds.

        Args:
            max_rows: Maximum number of rows
            max_cols: Maximum number of columns

        Returns:
            True if coordinate is valid
        """
        return 0 <= self.row < max_rows and 0 <= self.col < max_cols


class Hex:
    """Represents a single hex on the battle grid."""

    # Terrain movement costs
    TERRAIN_COSTS = {
        TerrainType.PLAINS: 2,
        TerrainType.FOREST: 3,
        TerrainType.HILLS: 3,
        TerrainType.CASTLE: 3,
        TerrainType.WATER: 5,
        TerrainType.MOUNTAIN: float("inf"),  # Impassable
        TerrainType.EMPTY: float("inf"),
    }

    def __init__(
        self,
        coord: HexCoord,
        terrain: TerrainType = TerrainType.PLAINS,
        terrain_code: int = 0,
    ):
        """
        Initialize a hex.

        Args:
            coord: Grid coordinate
            terrain: Terrain type
            terrain_code: Original terrain code from game data
        """
        self.coord = coord
        self.terrain = terrain
        self.terrain_code = (
            terrain_code  # Store original code for castle/fort differentiation
        )
        self.unit: Optional[Any] = None  # BattleUnit
        self.is_burning = False
        self.fire_age = 0  # Days the fire has been burning
        self.is_castle = False
        self.is_start_position = False

    def get_movement_cost(self) -> int:
        """
        Get movement cost for this hex.

        Returns:
            Movement cost (higher = harder to traverse)
        """
        return self.TERRAIN_COSTS.get(self.terrain, 2)

    def is_passable(self) -> bool:
        """
        Check if units can move through this hex.

        Returns:
            True if passable
        """
        if self.terrain == TerrainType.MOUNTAIN:
            return False
        if self.terrain == TerrainType.EMPTY:
            return False
        if self.is_burning:
            return False
        return True

    def can_enter(self) -> bool:
        """
        Check if a unit can enter this hex.

        Returns:
            True if unit can enter
        """
        if not self.is_passable():
            return False
        # Can't enter if occupied (except supplies can stack with friendlies)
        # This will be handled by BattleEngine
        return True

    def __repr__(self) -> str:
        """String representation."""
        return f"Hex({self.coord}, {self.terrain.name})"

    def set_burning(self, burning: bool = True):
        """
        Set whether this hex is on fire.

        Args:
            burning: True to set on fire, False to extinguish
        """
        if burning and not self.is_burning:
            # Starting new fire, reset age
            self.fire_age = 0
        elif not burning:
            # Extinguishing
            self.fire_age = 0
        self.is_burning = burning

    def try_extinguish(self) -> bool:
        """
        Try to extinguish the fire naturally.

        Natural extinguish chance = 0.18 + (age * 0.04)
        ~20% on turn 1, ~40% by turn 5-6

        Returns:
            True if fire was extinguished
        """
        if not self.is_burning:
            return False

        natural_extinguish_chance = 0.18 + (self.fire_age * 0.04)
        if random.random() < natural_extinguish_chance:
            self.set_burning(False)
            return True

        # Fire continues, increase age
        self.fire_age += 1
        return False

    def extinguish(self):
        """Immediately extinguish fire (e.g., from rain)."""
        self.set_burning(False)

    def can_catch_fire(self) -> bool:
        """
        Check if this hex can catch fire.

        Returns:
            True if can burn
        """
        if self.is_burning:
            return False
        if self.terrain in [TerrainType.WATER, TerrainType.EMPTY]:
            return False
        # Castles and forts CAN burn but are very resistant
        return True


class HexGrid:
    """
    12x13 hex grid for ROTK2 battles.

    Uses staggered row layout where odd columns are offset.
    """

    DEFAULT_ROWS = 12
    DEFAULT_COLS = 13

    def __init__(self, rows: int = DEFAULT_ROWS, cols: int = DEFAULT_COLS):
        """
        Initialize hex grid.

        Args:
            rows: Number of rows (default 12)
            cols: Number of columns (default 13)
        """
        self.rows = rows
        self.cols = cols
        self.hexes: Dict[HexCoord, Hex] = {}
        self._init_grid()

    def _init_grid(self):
        """Initialize empty grid with all hexes."""
        for row in range(self.rows):
            for col in range(self.cols):
                coord = HexCoord(row, col)
                self.hexes[coord] = Hex(coord, TerrainType.PLAINS)

    def load_from_province(self, province_id: int, data_dir: Path = None):
        """
        Load terrain data for a province.

        Args:
            province_id: Province number (1-41)
            data_dir: Path to data directory (default: ../../data)
        """
        if data_dir is None:
            data_dir = Path(__file__).parent.parent.parent / "data"

        terrain_file = data_dir / "terrain_data.json"
        if not terrain_file.exists():
            print(f"Warning: Terrain data file not found: {terrain_file}")
            return

        try:
            with open(terrain_file, "r", encoding="utf-8") as f:
                terrain_data = json.load(f)

            province_data = terrain_data.get(str(province_id))
            if not province_data:
                print(f"Warning: No terrain data for province {province_id}")
                return

            grid = province_data.get("terrain_grid", [])
            for row_idx, row_data in enumerate(grid):
                for col_idx, cell_data in enumerate(row_data):
                    if row_idx < self.rows and col_idx < self.cols:
                        coord = HexCoord(row_idx, col_idx)
                        terrain_code = cell_data.get("code", 0)
                        terrain = self._code_to_terrain(terrain_code)
                        self.hexes[coord].terrain = terrain
                        self.hexes[coord].terrain_code = terrain_code

        except Exception as e:
            print(f"Error loading terrain data: {e}")

    def _code_to_terrain(self, code: int) -> TerrainType:
        """
        Convert terrain code to TerrainType.

        Args:
            code: Terrain code from game data

        Returns:
            TerrainType enum
        """
        mapping = {
            0: TerrainType.PLAINS,
            1: TerrainType.FOREST,
            2: TerrainType.HILLS,
            3: TerrainType.MOUNTAIN,  # Code 3 is mountain
            4: TerrainType.WATER,  # Code 4 is water
            5: TerrainType.CASTLE,  # Code 5 is fort/mini-castle
            6: TerrainType.CASTLE,  # Code 6 is main castle
            9: TerrainType.MOUNTAIN,  # Edge
            99: TerrainType.EMPTY,
        }
        return mapping.get(code, TerrainType.PLAINS)

    def get_hex(self, coord: HexCoord) -> Optional[Hex]:
        """
        Get hex at coordinate.

        Args:
            coord: Hex coordinate

        Returns:
            Hex object or None if invalid
        """
        if not coord.is_valid(self.rows, self.cols):
            return None
        return self.hexes.get(coord)

    def get_adjacent(self, coord: HexCoord) -> List[HexCoord]:
        """
        Get all adjacent hex coordinates.

        In staggered hex grid, odd and even columns have different adjacencies.

        Args:
            coord: Center hex coordinate

        Returns:
            List of adjacent coordinates
        """
        row, col = coord.row, coord.col
        adjacent = []

        # In staggered grid, odd columns are offset
        if col % 2 == 0:  # Even column
            directions = [
                (-1, 0),  # Up
                (-1, 1),  # Up-Right
                (0, 1),  # Down-Right
                (1, 0),  # Down
                (0, -1),  # Down-Left
                (-1, -1),  # Up-Left
            ]
        else:  # Odd column
            directions = [
                (-1, 0),  # Up
                (0, 1),  # Up-Right
                (1, 1),  # Down-Right
                (1, 0),  # Down
                (1, -1),  # Down-Left
                (0, -1),  # Up-Left
            ]

        for d_row, d_col in directions:
            new_row = row + d_row
            new_col = col + d_col
            new_coord = HexCoord(new_row, new_col)
            if new_coord.is_valid(self.rows, self.cols):
                adjacent.append(new_coord)

        return adjacent

    def is_adjacent_to_enemy(self, coord: HexCoord, friendly_units: List[Any]) -> bool:
        """
        Check if hex is adjacent to any enemy units.

        Args:
            coord: Position to check
            friendly_units: List of friendly BattleUnits

        Returns:
            True if adjacent to enemy
        """
        adjacent_coords = self.get_adjacent(coord)
        friendly_ids = {id(unit) for unit in friendly_units}

        for adj_coord in adjacent_coords:
            hex_obj = self.get_hex(adj_coord)
            if hex_obj and hex_obj.unit:
                if id(hex_obj.unit) not in friendly_ids:
                    return True
        return False

    def get_movement_range(self, start: HexCoord, mobility: int) -> List[HexCoord]:
        """
        Calculate all hexes reachable with given mobility.

        Args:
            start: Starting position
            mobility: Movement points available

        Returns:
            List of reachable coordinates
        """
        reachable = set()
        visited = {start: 0}  # coord -> cost to reach
        queue = [(start, 0)]  # (coord, cost_so_far)

        while queue:
            current, cost_so_far = queue.pop(0)

            if cost_so_far >= mobility:
                continue

            for adj_coord in self.get_adjacent(current):
                hex_obj = self.get_hex(adj_coord)
                if not hex_obj or not hex_obj.is_passable():
                    continue

                move_cost = hex_obj.get_movement_cost()
                new_cost = cost_so_far + move_cost

                if new_cost <= mobility and (
                    adj_coord not in visited or new_cost < visited[adj_coord]
                ):
                    visited[adj_coord] = new_cost
                    reachable.add(adj_coord)
                    queue.append((adj_coord, new_cost))

        return list(reachable)

    def place_unit(self, unit: Any, coord: HexCoord) -> bool:
        """
        Place a unit on the grid.

        Args:
            unit: BattleUnit to place
            coord: Position to place at

        Returns:
            True if successful
        """
        hex_obj = self.get_hex(coord)
        if not hex_obj:
            return False

        if not hex_obj.can_enter():
            return False

        # Remove from old position if exists
        if unit.position:
            old_hex = self.get_hex(unit.position)
            if old_hex:
                old_hex.unit = None

        hex_obj.unit = unit
        unit.position = coord
        return True

    def remove_unit(self, coord: HexCoord) -> Optional[Any]:
        """
        Remove unit from grid.

        Args:
            coord: Position to remove from

        Returns:
            The removed unit or None
        """
        hex_obj = self.get_hex(coord)
        if not hex_obj or not hex_obj.unit:
            return None

        unit = hex_obj.unit
        unit.position = None
        hex_obj.unit = None
        return unit

    def __repr__(self) -> str:
        """String representation."""
        return f"HexGrid({self.rows}x{self.cols})"


if __name__ == "__main__":
    # Test the grid
    print("Testing HexGrid...")

    grid = HexGrid()
    print(f"Created grid: {grid}")

    # Test coordinate
    coord = HexCoord(5, 5)
    print(f"Coordinate: {coord}")
    print(f"Is valid: {coord.is_valid()}")

    # Test adjacency
    adjacent = grid.get_adjacent(coord)
    print(f"Adjacent to {coord}: {adjacent}")

    # Test hex retrieval
    hex_obj = grid.get_hex(coord)
    print(f"Hex at {coord}: {hex_obj}")
    print(f"Movement cost: {hex_obj.get_movement_cost()}")

    # Test movement range
    reachable = grid.get_movement_range(coord, 6)
    print(f"Reachable from {coord} with mobility 6: {len(reachable)} hexes")

    print("HexGrid test complete!")
