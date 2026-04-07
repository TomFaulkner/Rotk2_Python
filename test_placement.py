#!/usr/bin/env python3
"""
Test placement restrictions.
"""

import sys
import os
from pathlib import Path

# Change to Src directory
src_dir = Path(__file__).parent / "Src"
os.chdir(src_dir)
sys.path.insert(0, str(src_dir))

from Data import Data
from Officer import Officer
from Battle import BattleEngine, BattleUnit, HexCoord


def load_officer(officer_id: int) -> Officer:
    """Load officer by ID."""
    offset = Data.OFFICER_START + Data.OFFICER_SIZE * officer_id
    return Officer.FromBuffer(
        Data.BUF[offset : offset + Data.OFFICER_SIZE],
        officer_id,
        Data.BUF[0x45] * 256 + Data.BUF[0x44],
    )


def test_placement_restrictions():
    """Test placement zone restrictions."""
    print("=" * 60)
    print("Testing Placement Restrictions")
    print("=" * 60)

    # Create battle
    battle = BattleEngine(province_id=10, is_attacker=True)

    print(f"\n1. Castle position: {battle.defender_castle_pos}")
    print(f"2. Attacker direction: {battle.attacker_direction}")

    # Get valid placement zones
    attacker_zones = battle.get_valid_placement_hexes(is_attacker=True)
    defender_zones = battle.get_valid_placement_hexes(is_attacker=False)

    print(f"\n3. Attacker placement zones: {len(attacker_zones)} hexes")
    print("   (Should be on one edge of the map)")

    print(f"\n4. Defender placement zones: {len(defender_zones)} hexes")
    print("   (Should be within 3 hexes of castle)")

    # Test valid placement checks
    print("\n5. Testing placement validation:")

    # Test attacker placement
    if attacker_zones:
        valid_coord = attacker_zones[0]
        is_valid = battle.is_valid_placement(valid_coord, is_attacker=True)
        print(
            f"   Attacker zone {valid_coord}: {'✓ Valid' if is_valid else '✗ Invalid'}"
        )

        # Try castle position (should be invalid for attacker)
        if battle.defender_castle_pos:
            is_valid = battle.is_valid_placement(
                battle.defender_castle_pos, is_attacker=True
            )
            print(
                f"   Castle position for attacker: {'✓ Valid' if is_valid else '✗ Invalid (correct)'}"
            )

    # Test defender placement
    if defender_zones:
        valid_coord = defender_zones[0]
        is_valid = battle.is_valid_placement(valid_coord, is_attacker=False)
        print(
            f"   Defender zone {valid_coord}: {'✓ Valid' if is_valid else '✗ Invalid'}"
        )

    # Add units and test placement
    print("\n6. Testing actual unit placement:")

    officer = load_officer(0)
    unit = BattleUnit(officer, soldiers=50, is_attacker=True)
    battle.add_attacking_unit(unit)

    # Try valid placement
    if attacker_zones:
        result = battle.place_unit(unit, attacker_zones[0])
        print(
            f"   Placed at valid zone {attacker_zones[0]}: {'✓ Success' if result else '✗ Failed'}"
        )

    # Add defender
    officer2 = load_officer(1)
    unit2 = BattleUnit(officer2, soldiers=50, is_attacker=False)
    battle.add_defending_unit(unit2)

    if defender_zones:
        result = battle.place_unit(unit2, defender_zones[0])
        print(
            f"   Placed defender at valid zone {defender_zones[0]}: {'✓ Success' if result else '✗ Failed'}"
        )

    print("\n" + "=" * 60)
    print("Placement restriction test complete!")
    print("=" * 60)


if __name__ == "__main__":
    test_placement_restrictions()
