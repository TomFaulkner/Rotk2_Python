#!/usr/bin/env python3
"""
Quick battle test without graphics.

Tests the battle system logic without launching pygame.
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
from Battle import BattleEngine, BattleUnit, HexCoord, UnitState


def load_officer(officer_id: int) -> Officer:
    """Load officer by ID."""
    offset = Data.OFFICER_START + Data.OFFICER_SIZE * officer_id
    return Officer.FromBuffer(
        Data.BUF[offset : offset + Data.OFFICER_SIZE],
        officer_id,
        Data.BUF[0x45] * 256 + Data.BUF[0x44],
    )


def test_battle():
    """Run a quick battle test."""
    print("=" * 60)
    print("Quick Battle System Test")
    print("=" * 60)

    # Create battle
    print("\n1. Creating battle in province 10...")
    battle = BattleEngine(province_id=10, is_attacker=True)
    print(f"   ✓ Battle created")

    # Add defenders (first 5 officers)
    print("\n2. Adding defenders (officers 0-4):")
    for i in range(5):
        officer = load_officer(i)
        unit = BattleUnit(officer, soldiers=50 + i * 10, is_attacker=False)
        battle.add_defending_unit(unit)
        print(f"   {i + 1}. {unit.get_officer_name()} - {unit.soldiers} soldiers")

    # Add attackers (officers 5-9)
    print("\n3. Adding attackers (officers 5-9):")
    for i in range(5, 10):
        officer = load_officer(i)
        unit = BattleUnit(officer, soldiers=60 + (i - 5) * 10, is_attacker=True)
        battle.add_attacking_unit(unit)
        print(f"   {i - 4}. {unit.get_officer_name()} - {unit.soldiers} soldiers")

    # Set commanders
    defender_units = battle.get_defending_units_on_map()
    attacker_units = battle.get_attacking_units_on_map()

    if defender_units:
        battle.set_commander(defender_units[0], is_attacker=False)
        print(f"\n4. Defender Commander: {defender_units[0].get_officer_name()}")

    if attacker_units:
        battle.set_commander(attacker_units[0], is_attacker=True)
        print(f"   Attacker Commander: {attacker_units[0].get_officer_name()}")

    # Place units manually
    print("\n5. Placing units on grid:")

    # Defenders at bottom
    defender_positions = [
        HexCoord(9, 2),
        HexCoord(10, 4),
        HexCoord(9, 6),
        HexCoord(10, 8),
        HexCoord(9, 10),
    ]

    for i, unit in enumerate(defender_units[:5]):
        if i < len(defender_positions):
            battle.place_unit(unit, defender_positions[i])
            print(f"   {unit.get_officer_name()} at {defender_positions[i]}")

    # Attackers at top
    attacker_positions = [
        HexCoord(1, 2),
        HexCoord(2, 4),
        HexCoord(1, 6),
        HexCoord(2, 8),
        HexCoord(1, 10),
    ]

    for i, unit in enumerate(attacker_units[:5]):
        if i < len(attacker_positions):
            battle.place_unit(unit, attacker_positions[i])
            print(f"   {unit.get_officer_name()} at {attacker_positions[i]}")

    # Test movement
    print("\n6. Testing movement:")
    test_unit = attacker_units[0]
    print(f"   Testing unit: {test_unit.get_officer_name()}")
    print(f"   Position: {test_unit.position}")
    print(f"   Mobility: {test_unit.mobility}")

    reachable = battle.grid.get_movement_range(test_unit.position, test_unit.mobility)
    print(f"   Reachable hexes: {len(reachable)}")

    # Test adjacency
    print("\n7. Testing adjacency detection:")
    adjacent = battle.grid.get_adjacent(test_unit.position)
    print(f"   Adjacent hexes: {len(adjacent)}")

    # Check if adjacent to enemy
    enemy_units = battle.get_defending_units_on_map()
    is_adjacent = battle.grid.is_adjacent_to_enemy(test_unit.position, enemy_units)
    print(f"   Adjacent to enemy: {is_adjacent}")

    # Test attack
    print("\n8. Testing combat:")
    attacker = attacker_units[0]
    defender = defender_units[0]

    print(f"   {attacker.get_officer_name()} attacks {defender.get_officer_name()}")
    print(f"   Attacker power: {attacker.get_effective_attack():.1f}")
    print(f"   Defender power: {defender.get_effective_attack():.1f}")

    # Simulate attack
    defender_health_before = defender.soldiers
    damage = attacker.get_effective_attack()
    defender.take_damage(damage)
    defender_health_after = defender.soldiers

    print(f"   Damage dealt: {defender_health_before - defender_health_after}")
    print(f"   Defender soldiers: {defender_health_before} -> {defender_health_after}")

    # Test victory check
    print("\n9. Testing victory conditions:")
    result = battle.check_victory()
    if result:
        print(f"   Result: {result.name}")
    else:
        print("   Battle continues (no victory yet)")

    # Test battle summary
    print("\n10. Battle summary:")
    summary = battle.get_battle_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")

    print("\n" + "=" * 60)
    print("Battle system test complete!")
    print("=" * 60)

    return battle


if __name__ == "__main__":
    print("ROTK2 Battle System Quick Test\n")

    try:
        battle = test_battle()
        print("\n✓ All tests passed!")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
