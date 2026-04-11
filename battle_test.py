#!/usr/bin/env python3
"""
Battle Test Script

Launches a battle immediately for testing without playing through the game.
This file contains ONLY test-specific setup and features.
"""

import sys
import os
from pathlib import Path

# Change to Src directory for proper Data module loading
src_dir = Path(__file__).parent / "Src"
os.chdir(src_dir)
sys.path.insert(0, str(src_dir))

import pygame
from pygame.locals import *

from Data import Data
from Officer import Officer
from Battle import BattleEngine, BattleUnit, BattleGame
from Battle.battle_renderer import BattleRenderer
from config import get_settings, RiceDepletionMode


def load_officer_data(officer_id: int) -> Officer:
    """Load officer data by ID."""
    offset = Data.OFFICER_START + Data.OFFICER_SIZE * officer_id
    officer = Officer.FromBuffer(
        Data.BUF[offset : offset + Data.OFFICER_SIZE],
        officer_id,
        Data.BUF[0x45] * 256 + Data.BUF[0x44],
    )
    officer.Id = officer_id
    return officer


def create_test_battle(province_id: int = 10) -> BattleEngine:
    """Create a test battle with mock values."""
    settings = get_settings()
    print(f"Creating battle in province {province_id}...")

    # Display rice depletion mode
    mode_str = (
        "FORCE RETREAT"
        if settings.rice_depletion_mode == RiceDepletionMode.FORCE_RETREAT
        else "DESERTION"
    )
    print(f"\nRice Depletion Mode: {mode_str}")

    # Create battle
    battle = BattleEngine(province_id=province_id, is_attacker=True)

    # First 5 officers as defenders (on field)
    print("\nDefenders (first 5 officers on field):")
    for i in range(5):
        try:
            officer = load_officer_data(i)
            soldiers = 50 + (i * 10)
            unit = BattleUnit(officer, soldiers=soldiers, is_attacker=False)
            battle.add_defending_unit(unit)
            print(f"  {i + 1}. {unit.get_officer_name()} - {soldiers} soldiers")
        except Exception as e:
            print(f"  Error loading officer {i}: {e}")

    # Officers 10-15 as defender reserves (for reinforcement testing)
    print("\nDefender Reserves (officers 10-15):")
    for i in range(10, 16):
        try:
            officer = load_officer_data(i)
            soldiers = 40 + ((i - 10) * 8)
            unit = BattleUnit(officer, soldiers=soldiers, is_attacker=False)
            battle.defender_reserve.add(unit)
            print(f"  {i - 9}. {unit.get_officer_name()} - {soldiers} soldiers (reserve)")
        except Exception as e:
            print(f"  Error loading officer {i}: {e}")

    # Officers 5-10 as attackers
    print("\nAttackers (officers 5-10):")
    for i in range(5, 10):
        try:
            officer = load_officer_data(i)
            soldiers = 60 + ((i - 5) * 10)
            unit = BattleUnit(officer, soldiers=soldiers, is_attacker=True)
            battle.add_attacking_unit(unit)
            print(f"  {i - 4}. {unit.get_officer_name()} - {soldiers} soldiers")
        except Exception as e:
            print(f"  Error loading officer {i}: {e}")

    # Set commanders
    defender_units = battle.defending_units
    attacker_units = battle.attacking_units

    # Initialize rice supplies (test value: 10 days worth)
    attacker_troops = sum(u.soldiers for u in attacker_units)
    defender_troops = sum(u.soldiers for u in defender_units)
    daily_consumption_rate = settings.rice_consumption_rate
    battle.attacker_supplies["rice"] = (attacker_troops // daily_consumption_rate) * 10
    battle.defender_supplies["rice"] = (defender_troops // daily_consumption_rate) * 10

    print(f"\nSupplies:")
    print(f"  Attacker rice: {battle.attacker_supplies['rice']} (for {attacker_troops} troops)")
    print(f"  Defender rice: {battle.defender_supplies['rice']} (for {defender_troops} troops)")

    if defender_units:
        battle.set_commander(defender_units[0], is_attacker=False)
        print(f"\nDefender Commander: {defender_units[0].get_officer_name()}")

    if attacker_units:
        battle.set_commander(attacker_units[0], is_attacker=True)
        print(f"Attacker Commander: {attacker_units[0].get_officer_name()}")

    print(f"\nBattle ready!")
    return battle


class BattleTestGame(BattleGame):
    """
    Battle test game with test-specific features.

    Uses BattleGame with cheats=True to enable debug features:
    - W: Cycle wind direction
    - E: Force weather transition
    """

    def __init__(self, width: int = 1024, height: int = 768):
        # Initialize pygame
        pygame.init()
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("ROTK2 Battle Test")

        # Create test battle
        battle = create_test_battle(province_id=10)
        renderer = BattleRenderer(screen, tile_size=32)

        # Initialize base BattleGame with cheats enabled
        super().__init__(screen, battle, renderer, cheats=True)

        print("\n" + "=" * 50)
        print("TEST FEATURES:")
        print("  W - Cycle wind direction")
        print("  E - Force weather transition")
        print("  R - Call reinforcements (defender's turn only)")
        print("=" * 50)


def main():
    """Main entry point."""
    print("ROTK2 Battle Test")
    print("=================\n")

    try:
        game = BattleTestGame()
        game.run()
    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()

    print("\nBattle test complete!")


if __name__ == "__main__":
    main()
