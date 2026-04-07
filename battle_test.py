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
from Battle import BattleEngine, BattleUnit, BattleGame, BattleGamePhase
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

    # First 5 officers as defenders
    print("\nDefenders (first 5 officers):")
    for i in range(5):
        try:
            officer = load_officer_data(i)
            soldiers = 50 + (i * 10)
            unit = BattleUnit(officer, soldiers=soldiers, is_attacker=False)
            battle.add_defending_unit(unit)
            print(f"  {i + 1}. {unit.get_officer_name()} - {soldiers} soldiers")
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
    print(
        f"  Attacker rice: {battle.attacker_supplies['rice']} (for {attacker_troops} troops)"
    )
    print(
        f"  Defender rice: {battle.defender_supplies['rice']} (for {defender_troops} troops)"
    )

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

    Extends BattleGame to add:
    - Test features (force weather, cycle wind)
    - Custom initialization
    """

    def __init__(self, width: int = 1024, height: int = 768):
        # Initialize pygame
        pygame.init()
        screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("ROTK2 Battle Test")

        # Create test battle
        battle = create_test_battle(province_id=10)
        renderer = BattleRenderer(screen, hex_size=28)

        # Initialize base BattleGame
        super().__init__(screen, battle, renderer)

        print("\n" + "=" * 50)
        print("TEST FEATURES:")
        print("  W - Cycle wind direction")
        print("  E - Force weather transition")
        print("=" * 50)

    def handle_events(self):
        """Handle events with test features."""
        from pygame.locals import KEYDOWN, K_w, K_e

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == KEYDOWN:
                # Test features
                if event.key == K_w:
                    # Cycle wind direction (test feature)
                    directions = [None, "N", "NE", "SE", "S", "SW", "NW"]
                    current_idx = (
                        directions.index(self.battle.wind_direction)
                        if self.battle.wind_direction in directions
                        else -1
                    )
                    self.battle.wind_direction = directions[
                        (current_idx + 1) % len(directions)
                    ]
                    print(f"[TEST] Wind: {self.battle.wind_direction or 'Calm'}")
                    continue

                elif event.key == K_e:
                    # Force weather transition (test feature)
                    old_weather = self.battle.weather
                    new_weather = self.battle.transition_weather()
                    print(f"[TEST] Weather: {old_weather} -> {new_weather}")
                    continue

                # Pass other events to parent
                self._handle_keydown(event.key)

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._handle_click(event.pos)

    def _handle_keydown(self, key):
        """Handle keydown events (called from handle_events)."""
        from pygame.locals import K_ESCAPE, K_RETURN, K_SPACE, K_f, K_b

        if key == K_ESCAPE:
            self._handle_escape()
        elif key == K_SPACE:
            self._advance_placement()
        elif key == K_RETURN:
            self._handle_return()
        elif key == K_f:
            self._toggle_fire_mode()
        elif key == K_b:
            self._toggle_bribe_mode()
        else:
            # Handle other keys based on phase
            if (
                self.phase == BattleGamePhase.PERSONAL_COMBAT_OFFER
                or self.phase == BattleGamePhase.PERSONAL_COMBAT_SELECT
            ):
                self._handle_personal_combat_key(key)
            elif self.phase == BattleGamePhase.BRIBE_SELECT:
                self._handle_bribe_key(key)
            elif self.ui.attack_target:
                self._handle_attack_key(key)


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
