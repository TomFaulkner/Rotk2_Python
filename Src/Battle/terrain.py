"""
Terrain types and effects for battle maps.
"""

from typing import Dict


class Terrain:
    """
    Terrain type definitions and their properties.

    Based on SNES/PC version with simplified terrain types.
    """

    # Movement costs for each terrain type
    MOVEMENT_COSTS: Dict[str, int] = {
        "plains": 2,
        "forest": 3,
        "hills": 3,
        "castle": 3,
        "water": 5,
        "mountain": float("inf"),  # Impassable
        "empty": float("inf"),
    }

    # Defense bonuses (multipliers)
    DEFENSE_MULTIPLIERS: Dict[str, float] = {
        "plains": 1.0,
        "forest": 1.2,
        "hills": 1.3,
        "castle": 1.5,
        "water": 0.8,  # Vulnerable in water
        "mountain": 2.0,
        "empty": 1.0,
    }

    # Fire susceptibility (higher = easier to set on fire)
    FIRE_CHANCE: Dict[str, float] = {
        "plains": 0.7,
        "forest": 0.9,
        "hills": 0.5,
        "castle": 0.2,  # Hard to burn
        "water": 0.0,
        "mountain": 0.3,
        "empty": 0.0,
    }

    # Display names
    DISPLAY_NAMES: Dict[str, str] = {
        "plains": "Plains",
        "forest": "Forest",
        "hills": "Hills",
        "castle": "Castle",
        "water": "Water",
        "mountain": "Mountain",
        "empty": "Empty",
    }

    @classmethod
    def get_movement_cost(cls, terrain_type: str) -> int:
        """
        Get movement cost for terrain.

        Args:
            terrain_type: Type of terrain

        Returns:
            Movement cost (higher = harder to traverse)
        """
        return cls.MOVEMENT_COSTS.get(terrain_type, 2)

    @classmethod
    def get_defense_multiplier(cls, terrain_type: str) -> float:
        """
        Get defense multiplier for terrain.

        Args:
            terrain_type: Type of terrain

        Returns:
            Defense multiplier
        """
        return cls.DEFENSE_MULTIPLIERS.get(terrain_type, 1.0)

    @classmethod
    def get_fire_chance(cls, terrain_type: str) -> float:
        """
        Get base fire chance for terrain.

        Args:
            terrain_type: Type of terrain

        Returns:
            Fire chance (0.0 to 1.0)
        """
        return cls.FIRE_CHANCE.get(terrain_type, 0.5)

    @classmethod
    def get_display_name(cls, terrain_type: str) -> str:
        """
        Get display name for terrain.

        Args:
            terrain_type: Type of terrain

        Returns:
            Human readable name
        """
        return cls.DISPLAY_NAMES.get(terrain_type, terrain_type.title())

    @classmethod
    def is_passable(cls, terrain_type: str) -> bool:
        """
        Check if terrain is passable.

        Args:
            terrain_type: Type of terrain

        Returns:
            True if units can move through
        """
        return terrain_type not in ["mountain", "empty"]

    @classmethod
    def is_burnable(cls, terrain_type: str) -> bool:
        """
        Check if terrain can catch fire.

        Args:
            terrain_type: Type of terrain

        Returns:
            True if can burn
        """
        return cls.FIRE_CHANCE.get(terrain_type, 0) > 0


class TerrainType:
    """Terrain type constants."""

    PLAINS = "plains"
    FOREST = "forest"
    HILLS = "hills"
    CASTLE = "castle"
    WATER = "water"
    MOUNTAIN = "mountain"
    EMPTY = "empty"

    # Code mapping for loading from game data
    CODE_MAP = {
        0: PLAINS,
        1: FOREST,
        2: HILLS,
        3: WATER,
        4: CASTLE,
        5: MOUNTAIN,
        6: MOUNTAIN,  # Obstacle
        9: MOUNTAIN,  # Edge
        99: EMPTY,
    }

    @classmethod
    def from_code(cls, code: int) -> str:
        """
        Convert terrain code to type string.

        Args:
            code: Terrain code from game data

        Returns:
            Terrain type string
        """
        return cls.CODE_MAP.get(code, cls.PLAINS)


if __name__ == "__main__":
    # Test terrain
    print("Testing Terrain...")

    for terrain in ["plains", "forest", "hills", "castle", "water", "mountain"]:
        print(f"\n{terrain.upper()}:")
        print(f"  Movement cost: {Terrain.get_movement_cost(terrain)}")
        print(f"  Defense mult: {Terrain.get_defense_multiplier(terrain)}")
        print(f"  Fire chance: {Terrain.get_fire_chance(terrain)}")
        print(f"  Passable: {Terrain.is_passable(terrain)}")
        print(f"  Burnable: {Terrain.is_burnable(terrain)}")

    print("\nTerrain test complete!")
