#!/usr/bin/env python3
"""
Battle Test Script

Launches a battle immediately for testing without playing through the game.
Uses first 5 officers as defenders, officers 5-10 as attackers.
"""

import sys
import os
import json
import random
from pathlib import Path

# Change to Src directory for proper Data module loading
src_dir = Path(__file__).parent / "Src"
os.chdir(src_dir)
sys.path.insert(0, str(src_dir))

import pygame
from pygame.locals import *

from Data import Data
from Officer import Officer
from Battle import BattleEngine, BattleUnit, HexCoord, UnitState, BattlePhase
from Battle.battle_renderer import BattleRenderer
from Battle.combat_system import CombatSystem, AttackType
from Battle.officer_names import get_officer_name_cached


class MockRuler:
    """Mock ruler for battle setup."""

    def __init__(self, name="Test Ruler"):
        self.name = name


def load_officer_data(officer_id: int) -> Officer:
    """
    Load officer data by ID.

    Args:
        officer_id: Officer ID (0-254)

    Returns:
        Officer object with Id attribute set
    """
    offset = Data.OFFICER_START + Data.OFFICER_SIZE * officer_id
    officer = Officer.FromBuffer(
        Data.BUF[offset : offset + Data.OFFICER_SIZE],
        officer_id,
        Data.BUF[0x45] * 256 + Data.BUF[0x44],
    )
    # Store the officer ID for name lookup
    officer.Id = officer_id
    return officer


def create_battle_test(province_id: int = 10) -> BattleEngine:
    """
    Create a test battle with pre-selected officers.

    Args:
        province_id: Province to battle in (default 10)

    Returns:
        Configured BattleEngine
    """
    print(f"Creating battle in province {province_id}...")

    # Create battle
    battle = BattleEngine(province_id=province_id, is_attacker=True)

    # First 5 officers as defenders
    print("\nDefenders (first 5 officers):")
    for i in range(5):
        try:
            officer = load_officer_data(i)
            # Give them some soldiers
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

    # Set commanders (first unit on each side)
    defender_units = battle.get_defending_units_on_map()
    attacker_units = battle.get_attacking_units_on_map()

    if defender_units:
        battle.set_commander(defender_units[0], is_attacker=False)
        print(f"\nDefender Commander: {defender_units[0].get_officer_name()}")

    if attacker_units:
        battle.set_commander(attacker_units[0], is_attacker=True)
        print(f"Attacker Commander: {attacker_units[0].get_officer_name()}")

    print(f"\nBattle ready!")
    print(f"Attackers: {len(attacker_units)}")
    print(f"Defenders: {len(defender_units)}")

    return battle


class BattleTestGame:
    """Test game that runs the battle immediately."""

    def __init__(self, width: int = 1024, height: int = 768):
        """Initialize the test game."""
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("ROTK2 Battle Test")
        self.clock = pygame.time.Clock()
        self.running = True

        # Create battle
        self.battle = create_battle_test(province_id=10)

        # Create renderer
        self.renderer = BattleRenderer(self.screen, hex_size=28)

        # Game state
        self.phase = "placement"  # placement, battle, ended
        self.selected_unit: BattleUnit = None
        self.placement_side = "attacker"  # attacker places first, then defender
        self.reachable_hexes: list = []
        self.valid_placement_hexes: list = []  # Valid zones for current side
        self.adjacent_enemies: list = []  # Enemies adjacent to selected unit
        self.combat_log: list = []  # Combat messages

        # Attack selection state
        self.attack_target: BattleUnit = None  # Target being attacked
        self.attack_options: list = []  # Available attack types
        self.helping_allies: list = []  # Allies that can help with simultaneous attack

        # Fire attack mode - when True, clicking empty hexes starts fires
        self.fire_mode: bool = False
        self.weather: str = "sunny"  # sunny, light_clouds, dark_clouds, storm
        self.wind_direction: str = None  # Direction wind is blowing (for fire spread)

        # Personal combat system state (pre-battle phase)
        # ROTK2: Single duel between two selected generals (not all units)
        self.personal_combat_phase: bool = False
        self.personal_combat_step: str = "defender_offer"  # defender_offer, defender_select, attacker_response, attacker_select, resolve
        self.personal_combat_defender_general: BattleUnit = (
            None  # Defender's chosen general
        )
        self.personal_combat_attacker_general: BattleUnit = (
            None  # Attacker's chosen general
        )
        self.personal_combat_proposer: str = (
            None  # Who proposed: "defender" or "attacker"
        )

        # Weather transition probabilities (ROTK2 accurate)
        self.WEATHER_TRANSITIONS = {
            "sunny": {
                "sunny": 0.58,
                "light_clouds": 0.38,
                "dark_clouds": 0.04,
                "storm": 0.00,
            },
            "light_clouds": {
                "sunny": 0.04,
                "light_clouds": 0.61,
                "dark_clouds": 0.19,
                "storm": 0.16,
            },
            "dark_clouds": {
                "sunny": 0.00,
                "light_clouds": 0.04,
                "dark_clouds": 0.61,
                "storm": 0.35,
            },
            "storm": {
                "sunny": 0.19,
                "light_clouds": 0.07,
                "dark_clouds": 0.03,
                "storm": 0.71,
            },
        }

        # Calculate initial valid placement zones
        self.update_valid_placement_zones()
        self.defender_start_positions = [
            HexCoord(10, 2),
            HexCoord(9, 4),
            HexCoord(10, 6),
            HexCoord(9, 8),
            HexCoord(10, 10),
        ]

    def handle_events(self):
        """Handle input events."""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    if self.attack_target:
                        # Cancel attack selection
                        self.attack_target = None
                        self.attack_options = []
                        print("Attack cancelled")
                    else:
                        self.running = False
                elif self.phase == "personal_combat_offer":
                    # Personal combat sequence: defender offers first
                    self._handle_personal_combat_input(event.key)
                elif self.attack_target:
                    # Attack selection mode
                    if event.key == K_1 or event.key == K_KP1:
                        self.execute_attack(self.attack_target, "normal")
                        self.attack_target = None
                        self.attack_options = []
                    elif event.key == K_2 or event.key == K_KP2:
                        self.execute_attack(self.attack_target, "charge")
                        self.attack_target = None
                        self.attack_options = []
                    elif event.key == K_3 or event.key == K_KP3:
                        if "simultaneous" in self.attack_options:
                            self.execute_attack(self.attack_target, "simultaneous")
                            self.attack_target = None
                            self.attack_options = []
                    elif event.key == K_4 or event.key == K_KP4:
                        if "fire" in self.attack_options:
                            # Instead of immediate fire, enter fire targeting mode
                            self.attack_target = None
                            self.attack_options = []
                            self.fire_mode = True
                            print(
                                "\n>>> FIRE MODE: Click adjacent empty hex to set fire"
                            )
                elif event.key == K_f:
                    # Toggle fire mode
                    if self.phase == "battle" and self.selected_unit:
                        self.fire_mode = not self.fire_mode
                        if self.fire_mode:
                            print(
                                "\n>>> FIRE MODE: Click adjacent empty hex to set fire"
                            )
                        else:
                            print("Fire mode cancelled")
                elif event.key == K_w:
                    # Cycle wind direction
                    directions = [None, "N", "NE", "SE", "S", "SW", "NW"]
                    current_idx = (
                        directions.index(self.wind_direction)
                        if self.wind_direction in directions
                        else -1
                    )
                    self.wind_direction = directions[
                        (current_idx + 1) % len(directions)
                    ]
                    if self.wind_direction:
                        print(f"Wind direction: {self.wind_direction}")
                    else:
                        print("Wind: Calm")
                elif event.key == K_e:
                    # Force weather transition (for testing)
                    self.transition_weather()
                elif event.key == K_SPACE:
                    self.advance_placement()
                elif event.key == K_RETURN:
                    if self.phase == "placement":
                        self.start_battle()
                    elif self.phase == "battle":
                        self.end_turn()

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # Left click
                    self.handle_click(event.pos)

    def handle_click(self, pos: tuple):
        """Handle mouse click."""
        x, y = pos

        # Get hex at click position
        clicked_hex = self.renderer.get_hex_at_pixel(self.battle.grid, x, y)

        if not clicked_hex:
            return

        if self.phase == "placement":
            self.handle_placement_click(clicked_hex)
        elif self.phase == "personal_combat_offer":
            self.handle_personal_combat_click(clicked_hex)
        elif self.phase == "battle":
            self.handle_battle_click(clicked_hex)

    def update_valid_placement_zones(self):
        """Update the valid placement hexes for current side."""
        is_attacker = self.placement_side == "attacker"
        self.valid_placement_hexes = self.battle.get_valid_placement_hexes(is_attacker)

    def handle_placement_click(self, coord: HexCoord):
        """Handle click during placement phase."""
        # Check if click is in valid placement zone
        is_attacker = self.placement_side == "attacker"
        if not self.battle.is_valid_placement(coord, is_attacker):
            print(f"Invalid placement! Must place in designated zone.")
            return

        # Get next unplaced unit for current side
        if self.placement_side == "attacker":
            unplaced = [
                u for u in self.battle.attacking_units if u.state == UnitState.INACTIVE
            ]
        else:
            unplaced = [
                u for u in self.battle.defending_units if u.state == UnitState.INACTIVE
            ]

        if not unplaced:
            return

        # Place unit at clicked hex
        unit = unplaced[0]
        if self.battle.place_unit(unit, coord):
            print(f"Placed {unit.get_officer_name()} at {coord}")

            # Check if side is done placing
            if self.placement_side == "attacker":
                remaining = [
                    u
                    for u in self.battle.attacking_units
                    if u.state == UnitState.INACTIVE
                ]
                if not remaining:
                    self.placement_side = "defender"
                    self.update_valid_placement_zones()
                    print("\nDefender's turn to place units")
                    print(
                        f"Valid zones: {len(self.valid_placement_hexes)} hexes near castle"
                    )
            else:
                remaining = [
                    u
                    for u in self.battle.defending_units
                    if u.state == UnitState.INACTIVE
                ]
                if not remaining:
                    self.valid_placement_hexes = []
                    print("\nAll units placed! Press ENTER to start battle")

    def advance_placement(self):
        """Auto-place remaining units in valid zones."""
        is_attacker = self.placement_side == "attacker"

        if is_attacker:
            unplaced = [
                u for u in self.battle.attacking_units if u.state == UnitState.INACTIVE
            ]
        else:
            unplaced = [
                u for u in self.battle.defending_units if u.state == UnitState.INACTIVE
            ]

        # Get valid placement zones
        valid_hexes = self.battle.get_valid_placement_hexes(is_attacker)

        for i, unit in enumerate(unplaced):
            if i < len(valid_hexes):
                self.battle.place_unit(unit, valid_hexes[i])
                print(f"Auto-placed {unit.get_officer_name()} at {valid_hexes[i]}")

        # Switch side or start battle
        if self.placement_side == "attacker":
            self.placement_side = "defender"
            self.update_valid_placement_zones()
            print("\nDefender's turn to place units")
            print(f"Valid zones: {len(self.valid_placement_hexes)} hexes near castle")
        else:
            self.valid_placement_hexes = []
            print("\nAll units placed! Press ENTER to start battle")

    def start_battle(self):
        """Start the personal combat offer phase (before tactical battle)."""
        self.phase = "personal_combat_offer"
        self.personal_combat_phase = True
        self.personal_combat_step = "defender_offer"
        self.personal_combat_defender_general = None
        self.personal_combat_attacker_general = None
        self.personal_combat_proposer = None

        print("\n" + "=" * 60)
        print("PERSONAL COMBAT PHASE")
        print("=" * 60)
        print("\nThe defender is offered the first chance to propose personal combat.")
        print("If accepted, each side chooses ONE general to duel.")
        print("\nRefusing when the other side proposes:")
        print("  - 8% troop loss from ALL units!")
        print("\nDefender: Press Y to propose personal combat, N to decline")

    def _check_ambition_auto_accept(self):
        """Check if any generals auto-accept due to high ambition."""
        # Check attacker units
        for unit in self.battle.attacking_units:
            if unit.ambition >= 85:  # High ambition threshold
                self.attacker_accepted_personal_combat = True
                print(
                    f"\n>>> {unit.get_officer_name()} is eager for glory! (Ambition: {unit.ambition})"
                )
                print("Attacker side will engage in personal combat!")
                break

        # Check defender units
        for unit in self.battle.defending_units:
            if unit.ambition >= 85:
                print(
                    f"\n>>> {unit.get_officer_name()} seeks battle! (Ambition: {unit.ambition})"
                )
                print("This general may auto-accept challenges...")
                break

    def _handle_personal_combat_input(self, key):
        """Handle input during personal combat offer phase."""
        if self.personal_combat_step == "defender_offer":
            # Defender chooses to propose or not
            if key == K_y:
                # Defender proposes - now select their general
                self.personal_combat_proposer = "defender"
                self.personal_combat_step = "defender_select"
                print("\n>>> Defender proposes personal combat!")
                print("Select which general to send (click on unit)...")
            elif key == K_n:
                # Defender declines - offer to attacker
                self.personal_combat_step = "attacker_offer"
                print("\n>>> Defender declines to propose.")
                print("Attacker: Press Y to propose personal combat, N to decline")

        elif self.personal_combat_step == "attacker_offer":
            # Attacker chooses to propose or not
            if key == K_y:
                # Attacker proposes - now select their general
                self.personal_combat_proposer = "attacker"
                self.personal_combat_step = "attacker_select"
                print("\n>>> Attacker proposes personal combat!")
                print("Select which general to send (click on unit)...")
            elif key == K_n:
                # Both declined - skip to battle
                print("\n>>> Both sides decline personal combat.")
                print("Proceeding to tactical battle...")
                self._start_tactical_battle()

        elif self.personal_combat_step == "attacker_response":
            # Attacker responds to defender's proposal
            if key == K_y:
                # Attacker accepts - select their general
                self.personal_combat_step = "attacker_select"
                print("\n>>> Attacker ACCEPTS the challenge!")
                print("Select which general to send (click on unit)...")
            elif key == K_n:
                # Attacker refuses - penalty!
                print("\n>>> Attacker REFUSES the challenge!")
                print("The attacker's cowardice costs them dearly...")
                self._apply_desertion_penalty(is_attacker=True)
                self._start_tactical_battle()

        elif self.personal_combat_step == "defender_response":
            # Defender responds to attacker's proposal
            if key == K_y:
                # Defender accepts - select their general
                self.personal_combat_step = "defender_select"
                print("\n>>> Defender ACCEPTS the challenge!")
                print("Select which general to send (click on unit)...")
            elif key == K_n:
                # Defender refuses - penalty!
                print("\n>>> Defender REFUSES the challenge!")
                print("The defender's cowardice costs them dearly...")
                self._apply_desertion_penalty(is_attacker=False)
                self._start_tactical_battle()

        elif self.personal_combat_step == "defender_select":
            # Select defender general by number
            available = [u for u in self.battle.defending_units if not u.is_defeated()]
            if key == K_1 and len(available) >= 1:
                self._select_general_for_duel(available[0])
            elif key == K_2 and len(available) >= 2:
                self._select_general_for_duel(available[1])
            elif key == K_3 and len(available) >= 3:
                self._select_general_for_duel(available[2])
            elif key == K_4 and len(available) >= 4:
                self._select_general_for_duel(available[3])
            elif key == K_5 and len(available) >= 5:
                self._select_general_for_duel(available[4])
            elif key == K_RETURN and self.personal_combat_defender_general:
                self._check_personal_combat_ready()

        elif self.personal_combat_step == "attacker_select":
            # Select attacker general by number
            available = [u for u in self.battle.attacking_units if not u.is_defeated()]
            if key == K_1 and len(available) >= 1:
                self._select_general_for_duel(available[0])
            elif key == K_2 and len(available) >= 2:
                self._select_general_for_duel(available[1])
            elif key == K_3 and len(available) >= 3:
                self._select_general_for_duel(available[2])
            elif key == K_4 and len(available) >= 4:
                self._select_general_for_duel(available[3])
            elif key == K_5 and len(available) >= 5:
                self._select_general_for_duel(available[4])
            elif key == K_RETURN and self.personal_combat_attacker_general:
                self._check_personal_combat_ready()

    def _select_general_for_duel(self, unit: BattleUnit):
        """Select a general for personal combat."""
        if not unit or unit.is_defeated():
            return

        if self.personal_combat_step == "defender_select":
            if unit in self.battle.defending_units:
                self.personal_combat_defender_general = unit
                print(
                    f"\n{unit.get_officer_name()} selected for combat (War {unit.get_war_ability()})"
                )

                if self.personal_combat_proposer == "defender":
                    # Defender proposed, now attacker must respond
                    self.personal_combat_step = "attacker_response"
                    print(f"\n{unit.get_officer_name()} challenges the attacker!")
                    print("Attacker: Press Y to accept, N to refuse")
                else:
                    # Attacker proposed, defender already selected
                    self._check_personal_combat_ready()
            else:
                print("Select a defender unit!")

        elif self.personal_combat_step == "attacker_select":
            if unit in self.battle.attacking_units:
                self.personal_combat_attacker_general = unit
                print(
                    f"\n{unit.get_officer_name()} selected for combat (War {unit.get_war_ability()})"
                )

                if self.personal_combat_proposer == "attacker":
                    # Attacker proposed, now defender must respond
                    self.personal_combat_step = "defender_response"
                    print(f"\n{unit.get_officer_name()} challenges the defender!")
                    print("Defender: Press Y to accept, N to refuse")
                else:
                    # Defender proposed, attacker already selected
                    self._check_personal_combat_ready()
            else:
                print("Select an attacker unit!")

    def _check_personal_combat_ready(self):
        """Check if both generals are selected and resolve the duel."""
        if (
            self.personal_combat_defender_general
            and self.personal_combat_attacker_general
        ):
            self._resolve_single_duel()
        elif self.personal_combat_step == "defender_select":
            print("Select your general first!")
        elif self.personal_combat_step == "attacker_select":
            print("Select your general first!")

    def _resolve_single_duel(self):
        """Resolve the single duel between chosen generals."""
        from Battle.combat_system import CombatSystem

        att = self.personal_combat_attacker_general
        defe = self.personal_combat_defender_general

        print("\n" + "=" * 60)
        print("PERSONAL COMBAT BEGINS!")
        print("=" * 60)
        print(
            f"\n{att.get_officer_name()} (War {att.get_war_ability()}) vs {defe.get_officer_name()} (War {defe.get_war_ability()})"
        )
        print("-" * 60)

        # Resolve the duel
        result = CombatSystem.resolve_duel(att, defe)

        # Show round-by-round
        for round_data in result["rounds"]:
            rnd = round_data["round"]
            att_dmg = round_data["att_damage"]
            def_dmg = round_data["def_damage"]
            att_stam = round_data["att_stamina"]
            def_stam = round_data["def_stamina"]
            att_war = round_data["att_war"]
            def_war = round_data["def_war"]

            print(f"\nRound {rnd}:")
            print(
                f"  {att.get_officer_name()} deals {att_dmg} dmg | {defe.get_officer_name()} deals {def_dmg} dmg"
            )
            print(
                f"  {att.get_officer_name()}: War={att_war} Stam={att_stam} | {defe.get_officer_name()}: War={def_war} Stam={def_stam}"
            )

        # Show final result
        print("\n" + "=" * 60)
        print(result["message"])

        if result["war_gained"]:
            print(result["war_message"])

        # Apply consequences
        if result["result"] == "win":
            print(f"\n{defe.get_officer_name()} is captured!")
            defe.state = UnitState.CAPTURED
            if defe.position:
                self.battle.grid.remove_unit(defe.position)
        elif result["result"] == "loss":
            print(f"\n{att.get_officer_name()} is defeated!")
            att.state = UnitState.DEFEATED
            if att.position:
                self.battle.grid.remove_unit(att.position)
        else:
            print("\nBoth warriors survive the duel!")

        print("=" * 60)

        # Move to tactical battle
        self._start_tactical_battle()

    def _start_tactical_battle(self):
        """Start the tactical battle phase after personal combat."""
        self.phase = "battle"
        self.battle.phase = BattlePhase.TACTICAL
        self.personal_combat_phase = False
        print("\n>>> TACTICAL BATTLE BEGINS <<<")
        print("Click units to select, click hexes to move")
        print("Press ENTER to end turn")

    def _apply_desertion_penalty(self, is_attacker: bool):
        """Apply 8% desertion penalty to all units on one side."""
        from Battle.combat_system import CombatSystem

        units = (
            self.battle.attacking_units if is_attacker else self.battle.defending_units
        )
        side_name = "Attacker" if is_attacker else "Defender"
        total_deserted = 0

        print(f"\n{side_name} desertions:")
        for unit in units:
            if not unit.is_defeated():
                deserted = CombatSystem.calculate_refuse_penalty(unit)
                unit.soldiers -= deserted
                total_deserted += deserted
                print(
                    f"  {unit.get_officer_name()}: {deserted} soldiers deserted ({unit.soldiers} remain)"
                )

                if unit.soldiers <= 0:
                    print(f"  {unit.get_officer_name()}'s unit disbands!")
                    unit.state = UnitState.DEFEATED
                    if unit.position:
                        self.battle.grid.remove_unit(unit.position)

        print(f"\nTotal deserted: {total_deserted}")

    def handle_personal_combat_click(self, coord: HexCoord):
        """Handle clicking to select a general for personal combat."""
        hex_obj = self.battle.grid.get_hex(coord)
        if not hex_obj or not hex_obj.unit:
            return

        unit = hex_obj.unit

        # Check if selecting correct side's unit
        if self.personal_combat_step == "defender_select":
            if unit in self.battle.defending_units and not unit.is_defeated():
                self._select_general_for_duel(unit)
            else:
                print("Select a defender unit!")

        elif self.personal_combat_step == "attacker_select":
            if unit in self.battle.attacking_units and not unit.is_defeated():
                self._select_general_for_duel(unit)
            else:
                print("Select an attacker unit!")

    def handle_battle_click(self, coord: HexCoord):
        """Handle click during battle phase."""
        # Check if in fire mode
        if self.fire_mode and self.selected_unit:
            self.handle_fire_click(coord)
            return

        # Check if clicked on a unit
        hex_obj = self.battle.grid.get_hex(coord)

        if hex_obj and hex_obj.unit:
            unit = hex_obj.unit

            # Check if clicking on enemy (for attack)
            if (
                self.selected_unit
                and unit.is_attacker != self.selected_unit.is_attacker
                and not unit.is_defeated()
            ):
                # Check if adjacent
                if unit in self.adjacent_enemies:
                    self.start_attack_selection(unit)
                    return

            # Select unit
            self.selected_unit = unit
            print(f"Selected: {self.selected_unit.get_officer_name()}")

            # Calculate movement range
            if self.selected_unit.can_move():
                self.reachable_hexes = self.battle.grid.get_movement_range(
                    coord, self.selected_unit.mobility
                )
            else:
                self.reachable_hexes = []

            # Find adjacent enemies
            all_units = self.battle.get_all_units_on_map()
            self.adjacent_enemies = CombatSystem.get_adjacent_enemies(
                self.selected_unit, self.battle.grid, all_units
            )

            if self.adjacent_enemies:
                enemy_names = ", ".join(
                    e.get_officer_name() for e in self.adjacent_enemies
                )
                print(f"  Adjacent enemies: {enemy_names}")
                print(f"  Click enemy to attack!")

        elif self.selected_unit and self.selected_unit.can_move():
            # Try to move to clicked hex
            if coord in self.reachable_hexes:
                self.execute_move(coord)

        elif self.selected_unit and self.selected_unit.can_move():
            # Try to move to clicked hex
            if coord in self.reachable_hexes:
                old_pos = self.selected_unit.position
                if self.battle.grid.place_unit(self.selected_unit, coord):
                    # Calculate cost
                    hex_obj = self.battle.grid.get_hex(coord)
                    cost = hex_obj.get_movement_cost()
                    self.selected_unit.move_to(coord, cost)

                    # Check adjacency
                    enemy_units = (
                        self.battle.get_defending_units_on_map()
                        if self.selected_unit.is_attacker
                        else self.battle.get_attacking_units_on_map()
                    )

                    if self.battle.grid.is_adjacent_to_enemy(coord, enemy_units):
                        self.selected_unit.engage()
                        print(
                            f"Engaged enemy! Turn ends for {self.selected_unit.get_officer_name()}"
                        )

                    print(f"Moved to {coord}")
                    self.reachable_hexes = []

    def execute_move(self, coord: HexCoord):
        """Execute movement to coordinate."""
        old_pos = self.selected_unit.position
        if self.battle.grid.place_unit(self.selected_unit, coord):
            # Calculate cost
            hex_obj = self.battle.grid.get_hex(coord)
            cost = hex_obj.get_movement_cost()
            self.selected_unit.move_to(coord, cost)

            # Check adjacency
            enemy_units = (
                self.battle.get_defending_units_on_map()
                if self.selected_unit.is_attacker
                else self.battle.get_attacking_units_on_map()
            )

            if self.battle.grid.is_adjacent_to_enemy(coord, enemy_units):
                self.selected_unit.engage()
                print(
                    f"Engaged enemy! Turn ends for {self.selected_unit.get_officer_name()}"
                )

            print(f"Moved to {coord}")
            self.reachable_hexes = []

            # Update adjacent enemies
            all_units = self.battle.get_all_units_on_map()
            self.adjacent_enemies = CombatSystem.get_adjacent_enemies(
                self.selected_unit, self.battle.grid, all_units
            )

    def start_attack_selection(self, target_unit):
        """Start attack selection mode."""
        if not self.selected_unit or not self.selected_unit.can_attack():
            print("Cannot attack!")
            return

        # Check for simultaneous attack opportunity
        all_units = self.battle.get_all_units_on_map()
        adjacent_allies = CombatSystem.get_adjacent_allies(
            self.selected_unit, self.battle.grid, all_units
        )

        # Filter allies that can attack the same target
        self.helping_allies = []
        for ally in adjacent_allies:
            if ally.can_attack() and target_unit in CombatSystem.get_adjacent_enemies(
                ally, self.battle.grid, all_units
            ):
                self.helping_allies.append(ally)

        self.attack_target = target_unit
        self.attack_options = ["normal", "charge"]
        if self.helping_allies:
            self.attack_options.append("simultaneous")
        # Fire attack is always available (on empty hexes adjacent to enemies)
        self.attack_options.append("fire")

        print(f"\nSelect attack type against {target_unit.get_officer_name()}:")
        print("  1 - Normal Attack")
        print("  2 - Charge Attack")
        if self.helping_allies:
            ally_names = ", ".join(a.get_officer_name() for a in self.helping_allies)
            print(f"  3 - Simultaneous Attack (with {ally_names})")
        print("  4 - Fire Attack (adjacent hex)")
        print("  ESC - Cancel")

    def execute_attack(self, target_unit, attack_type: str = "normal"):
        """Execute attack on target unit with selected attack type."""
        if not self.selected_unit or not self.selected_unit.can_attack():
            print("Cannot attack!")
            return

        all_units = self.battle.get_all_units_on_map()

        # Execute based on attack type
        if attack_type == "fire":
            # Fire attack - target hex adjacent to enemy
            self.execute_fire_attack(target_unit)
            return
        elif attack_type == "simultaneous" and self.helping_allies:
            # Use simultaneous attack
            attackers = [self.selected_unit] + self.helping_allies
            result = CombatSystem.calculate_simultaneous_attack(
                attackers, target_unit, self.battle.grid
            )
            print(f"\n>>> SIMULTANEOUS ATTACK!")
        elif attack_type == "charge":
            # Charge attack
            result = CombatSystem.calculate_charge_attack(
                self.selected_unit, target_unit, self.battle.grid
            )
            print(f"\n>>> CHARGE ATTACK!")

            # Handle pass-through if successful
            if hasattr(result, "pass_through_hex") and result.pass_through_hex:
                # Move attacker to the hex behind defender
                old_pos = self.selected_unit.position
                if self.battle.grid.place_unit(
                    self.selected_unit, result.pass_through_hex
                ):
                    print(
                        f"  {self.selected_unit.get_officer_name()} charges through to {result.pass_through_hex}!"
                    )
        else:
            # Normal attack
            result = CombatSystem.calculate_normal_attack(
                self.selected_unit, target_unit, self.battle.grid
            )
            print(f"\n>>> NORMAL ATTACK")

        # Print results
        for msg in result.messages:
            print(f"  {msg}")

        # Mark attacker as having attacked
        self.selected_unit.has_attacked = True

        # Update combat log
        self.combat_log.extend(result.messages)

        # Clear defeated units from grid
        if result.defender_defeated:
            self.battle.grid.remove_unit(target_unit.position)
            print(f"  {target_unit.get_officer_name()} removed from battlefield")

        if result.attacker_defeated:
            self.battle.grid.remove_unit(self.selected_unit.position)
            print(f"  {self.selected_unit.get_officer_name()} defeated!")
            self.selected_unit = None

        # Update adjacent enemies
        if self.selected_unit:
            self.adjacent_enemies = CombatSystem.get_adjacent_enemies(
                self.selected_unit, self.battle.grid, all_units
            )

        # Check victory
        victory = self.battle.check_victory()
        if victory:
            self.phase = "ended"
            print(f"\n*** BATTLE ENDED: {victory.name} ***")

    def execute_fire_attack(self, target_unit):
        """Execute fire attack on hex adjacent to target unit."""
        if not self.selected_unit or not self.selected_unit.can_attack():
            print("Cannot use fire attack!")
            return

        # Find a burnable hex adjacent to both the attacker and target
        # Ideally behind the target from attacker's perspective
        attacker_pos = self.selected_unit.position
        target_pos = target_unit.position

        # Calculate direction from attacker to target
        dx = target_pos.col - attacker_pos.col
        dy = target_pos.row - attacker_pos.row

        # Try hex behind target first
        behind_col = target_pos.col + dx
        behind_row = target_pos.row + dy
        behind_hex = HexCoord(behind_row, behind_col)

        # Check adjacent hexes to target for burnable spots
        burnable_hexes = []
        adjacent_to_target = self.battle.grid.get_adjacent(target_pos)

        for coord in adjacent_to_target:
            hex_obj = self.battle.grid.get_hex(coord)
            if hex_obj and hex_obj.can_catch_fire():
                burnable_hexes.append(coord)

        if not burnable_hexes:
            print("No burnable hexes adjacent to target!")
            return

        # Prefer hex behind target
        target_hex = behind_hex if behind_hex in burnable_hexes else burnable_hexes[0]

        # Calculate fire success
        success, message, spread_hexes = CombatSystem.calculate_fire_success(
            self.selected_unit, target_hex, self.battle.grid
        )

        print(f"\n>>> FIRE ATTACK!")
        print(f"  {message}")
        print(f"  Intelligence: {self.selected_unit.get_intelligence()}")

        # Mark as attacked
        self.selected_unit.has_attacked = True

        # Add to combat log
        self.combat_log.append(f"Fire attack: {message}")

        # Check if any units are now on burning hexes and take damage
        all_units = self.battle.get_all_units_on_map()
        for unit in all_units:
            if unit.position:
                hex_obj = self.battle.grid.get_hex(unit.position)
                if hex_obj and hex_obj.is_burning:
                    # Unit takes fire damage
                    fire_damage = 10 + random.randint(0, 10)
                    casualties = unit.take_damage(fire_damage)
                    print(
                        f"  {unit.get_officer_name()} takes {casualties} fire damage!"
                    )
                    if unit.is_defeated():
                        print(f"  {unit.get_officer_name()} burned to death!")
                        self.battle.grid.remove_unit(unit.position)

        # Update adjacent enemies
        if self.selected_unit:
            self.adjacent_enemies = CombatSystem.get_adjacent_enemies(
                self.selected_unit, self.battle.grid, all_units
            )

    def handle_fire_click(self, coord: HexCoord):
        """Handle click in fire mode to set hex on fire."""
        if not self.selected_unit or not self.selected_unit.can_attack():
            print("Cannot use fire attack!")
            self.fire_mode = False
            return

        # Check if hex is adjacent
        adjacent = self.battle.grid.get_adjacent(self.selected_unit.position)
        if coord not in adjacent:
            print("Can only set fire on adjacent hexes!")
            return

        # Check if hex can catch fire
        hex_obj = self.battle.grid.get_hex(coord)
        if not hex_obj:
            print("Invalid hex!")
            return
        if not hex_obj.can_catch_fire():
            print("Cannot set fire on this terrain!")
            return

        # Try to start fire
        success, message, _ = CombatSystem.calculate_fire_success(
            self.selected_unit,
            coord,
            self.battle.grid,
            weather=self.weather,
            wind_direction=self.wind_direction,
        )

        print(f"\n>>> FIRE ATTACK!")
        print(f"  {message}")
        print(f"  Intelligence: {self.selected_unit.get_intelligence()}")
        if self.weather != "clear":
            print(f"  Weather: {self.weather}")

        if success:
            # Mark as attacked
            self.selected_unit.has_attacked = True
            self.combat_log.append(f"Fire: {message}")

            # Check if any units are now on burning hexes
            all_units = self.battle.get_all_units_on_map()
            for unit in all_units:
                if unit.position == coord:
                    fire_damage = 10 + random.randint(0, 10)
                    casualties = unit.take_damage(fire_damage)
                    print(
                        f"  {unit.get_officer_name()} takes {casualties} fire damage!"
                    )
                    if unit.is_defeated():
                        print(f"  {unit.get_officer_name()} burned to death!")
                        self.battle.grid.remove_unit(unit.position)

        # Exit fire mode
        self.fire_mode = False

    def end_turn(self):
        """End current turn."""
        # Reset all units
        for unit in self.battle.get_all_units_on_map():
            unit.end_turn()

        # Remember whose turn it was before advancing
        was_attacker_turn = self.battle.turn == 0

        # Advance battle turn
        self.battle.next_turn()

        # Check if a new day started (attacker's turn again)
        # Weather changes and fire spreads/extinguishes at the start of each day
        if self.battle.turn == 0 and not was_attacker_turn:
            print("\n>>> A new day begins...")

            # Weather transitions automatically each day
            old_weather = self.weather
            self.transition_weather()
            if self.weather != old_weather:
                print(
                    f"  Weather: {old_weather.replace('_', ' ').title()} -> {self.weather.replace('_', ' ').title()}"
                )

            new_fires, extinguished = CombatSystem.process_fires(
                self.battle.grid, self.wind_direction, self.weather
            )

            # Report extinguished fires
            if extinguished:
                for coord, msg in extinguished:
                    print(f"  {msg}")
                    self.combat_log.append(msg)

            # Report new fires
            if new_fires:
                for coord, msg in new_fires:
                    print(f"  {msg}")
                    self.combat_log.append(msg)

            # Units on burning hexes take damage
            all_units = self.battle.get_all_units_on_map()
            for unit in all_units:
                if unit.position:
                    hex_obj = self.battle.grid.get_hex(unit.position)
                    if hex_obj and hex_obj.is_burning:
                        fire_damage = 10 + random.randint(0, 10)
                        casualties = unit.take_damage(fire_damage)
                        print(
                            f"  {unit.get_officer_name()} takes {casualties} fire damage from burning hex!"
                        )
                        if unit.is_defeated():
                            print(f"  {unit.get_officer_name()} burned to death!")
                            self.battle.grid.remove_unit(unit.position)

        self.selected_unit = None
        self.reachable_hexes = []
        self.adjacent_enemies = []
        self.fire_mode = False

        print(
            f"\nTurn ended. Day {self.battle.day}, {'Attacker' if self.battle.turn == 0 else 'Defender'}'s turn"
        )

        # Check victory
        result = self.battle.check_victory()
        if result:
            self.phase = "ended"
            print(f"\n=== BATTLE ENDED ===")
            print(f"Result: {result.name}")

    def transition_weather(self):
        """
        Transition weather based on ROTK2 probability matrix.
        Called automatically at the start of each day.
        """
        transitions = self.WEATHER_TRANSITIONS.get(
            self.weather, self.WEATHER_TRANSITIONS["sunny"]
        )

        r = random.random()
        cumulative = 0.0
        new_weather = self.weather

        for weather, prob in transitions.items():
            cumulative += prob
            if r <= cumulative:
                new_weather = weather
                break

        # Check if storm (rain) just started - extinguishes all fires
        if new_weather == "storm" and self.weather != "storm":
            extinguished = []
            for coord, hex_obj in self.battle.grid.hexes.items():
                if hex_obj.is_burning:
                    hex_obj.extinguish()
                    extinguished.append(coord)
            if extinguished:
                print(f">>> Storm extinguishes all {len(extinguished)} fires!")
                for coord in extinguished:
                    self.combat_log.append(f"Storm extinguished fire at {coord}")

        self.weather = new_weather

    def update(self):
        """Update game state."""
        pass  # No continuous updates needed for now

    def render(self):
        """Render the game."""
        # Get all units
        all_units = self.battle.get_all_units_on_map()

        # Show valid placement zones during placement
        highlight_hexes = self.reachable_hexes.copy()

        # Add adjacent enemies to highlights (in red)
        if self.phase == "battle" and self.selected_unit and self.adjacent_enemies:
            for enemy in self.adjacent_enemies:
                if enemy.position:
                    highlight_hexes.append(enemy.position)

        # Render battle
        self.renderer.render(
            self.battle.grid,
            all_units,
            self.selected_unit,
            highlight_hexes,
            self.battle,
        )

        # Render valid placement zones
        if self.phase == "placement" and self.valid_placement_hexes:
            self.render_placement_zones()

        # Render adjacent enemy markers
        if self.phase == "battle" and self.adjacent_enemies:
            self.render_combat_markers()

        # Render combat log
        if self.combat_log:
            self.render_combat_log()

        # Render personal combat offer
        if self.phase == "personal_combat_offer":
            self.render_personal_combat_offer()

        # Render fire mode indicator
        if self.fire_mode:
            self.render_fire_mode_indicator()

        # Render wind direction
        if self.phase == "battle":
            self.render_wind_direction()

        # Render placement instructions
        if self.phase == "placement":
            self.render_placement_instructions()
        elif self.phase == "battle":
            self.render_battle_instructions()
        elif self.phase == "ended":
            self.render_end_screen()

        pygame.display.flip()

    def render_placement_zones(self):
        """Render valid placement zones."""
        import pygame

        # Draw semi-transparent highlights on valid placement hexes
        for coord in self.valid_placement_hexes:
            points = self.renderer.get_hex_polygon(coord)
            # Create a surface for transparency
            s = pygame.Surface(
                (self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA
            )
            color = (
                (0, 255, 0, 64)
                if self.placement_side == "attacker"
                else (255, 255, 0, 64)
            )
            pygame.draw.polygon(s, color, points)
            self.screen.blit(s, (0, 0))

            # Draw border
            pygame.draw.polygon(
                self.screen,
                (0, 200, 0) if self.placement_side == "attacker" else (200, 200, 0),
                points,
                2,
            )

    def render_placement_instructions(self):
        """Render placement phase UI."""
        y = self.screen.get_height() - 120

        # Semi-transparent background
        s = pygame.Surface((400, 110))
        s.set_alpha(200)
        s.fill((0, 0, 0))
        self.screen.blit(s, (10, y))

        font = pygame.font.SysFont(None, 24)
        small_font = pygame.font.SysFont(None, 20)

        # Title
        side = "Attacker" if self.placement_side == "attacker" else "Defender"
        text = font.render(f"PLACEMENT PHASE - {side}'s turn", True, (255, 255, 255))
        self.screen.blit(text, (20, y + 5))

        # Zone info
        if self.placement_side == "attacker":
            zone_text = "Place on green edge zones (attack direction)"
        else:
            zone_text = f"Place in yellow zones near castle ({len(self.valid_placement_hexes)} valid)"

        text = small_font.render(zone_text, True, (255, 255, 0))
        self.screen.blit(text, (20, y + 28))

        # Instructions
        lines = [
            "Click hexes to place units",
            "SPACE: Auto-place remaining",
            "ENTER: Start battle",
            "ESC: Exit",
        ]

        for i, line in enumerate(lines):
            text = small_font.render(line, True, (200, 200, 200))
            self.screen.blit(text, (20, y + 45 + i * 18))

    def render_battle_instructions(self):
        """Render battle phase UI."""
        y = self.screen.get_height() - 100

        s = pygame.Surface((400, 90))
        s.set_alpha(200)
        s.fill((0, 0, 0))
        self.screen.blit(s, (10, y))

        font = pygame.font.SysFont(None, 20)
        small_font = pygame.font.SysFont(None, 18)

        lines = [
            "BATTLE PHASE",
            "Click unit to select, click hex to move",
            "ENTER: End | ESC: Exit | F: Fire | D: Duel (Day 1)",
        ]

        for i, line in enumerate(lines):
            text = font.render(line, True, (255, 255, 255))
            self.screen.blit(text, (20, y + 10 + i * 20))

    def render_fire_mode_indicator(self):
        """Render fire mode indicator."""
        import pygame

        font = pygame.font.SysFont(None, 28)
        text = font.render("FIRE MODE - Click adjacent hex", True, (255, 100, 0))
        x = (self.screen.get_width() - text.get_width()) // 2
        self.screen.blit(text, (x, 50))

    def render_personal_combat_offer(self):
        """Render personal combat offer phase UI."""
        import pygame

        # Darken screen
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Dialog box
        box_width = 500
        box_height = 300
        x = (self.screen.get_width() - box_width) // 2
        y = (self.screen.get_height() - box_height) // 2

        s = pygame.Surface((box_width, box_height))
        s.set_alpha(240)
        s.fill((40, 20, 20))
        self.screen.blit(s, (x, y))

        # Border
        pygame.draw.rect(self.screen, (200, 50, 50), (x, y, box_width, box_height), 3)

        font = pygame.font.SysFont(None, 28)
        small_font = pygame.font.SysFont(None, 20)

        # Title
        title = font.render("PERSONAL COMBAT PHASE", True, (255, 100, 100))
        self.screen.blit(title, (x + 20, y + 15))

        # Show current step
        if self.personal_combat_step == "defender_offer":
            lines = [
                "The defender is offered the first chance",
                "to propose personal combat.",
                "",
                "One general from each side will duel.",
                "Refusing when challenged: 8% troop loss!",
            ]
            for i, line in enumerate(lines):
                text = small_font.render(line, True, (220, 220, 220))
                self.screen.blit(text, (x + 20, y + 50 + i * 18))

            text = font.render(
                "Defender: Propose personal combat?", True, (255, 255, 255)
            )
            self.screen.blit(text, (x + 20, y + 150))
            text = small_font.render("[Y] Yes  [N] No", True, (200, 200, 200))
            self.screen.blit(text, (x + 40, y + 175))

        elif self.personal_combat_step == "defender_select":
            lines = [
                "Defender has proposed personal combat!",
                "",
                "Select your champion:",
            ]
            for i, line in enumerate(lines):
                text = small_font.render(line, True, (220, 220, 220))
                self.screen.blit(text, (x + 20, y + 50 + i * 18))

            # List available defender generals
            available = [u for u in self.battle.defending_units if not u.is_defeated()]
            for i, unit in enumerate(available[:5]):  # Show up to 5
                name = unit.get_officer_name()
                war = unit.get_war_ability()
                text = small_font.render(
                    f"[{i + 1}] {name} (War {war})", True, (200, 200, 200)
                )
                self.screen.blit(text, (x + 40, y + 110 + i * 20))

            if self.personal_combat_defender_general:
                name = self.personal_combat_defender_general.get_officer_name()
                war = self.personal_combat_defender_general.get_war_ability()
                text = font.render(
                    f"Selected: {name} (War {war})", True, (100, 255, 100)
                )
                self.screen.blit(text, (x + 20, y + 220))
                text = small_font.render("Press ENTER to confirm", True, (255, 255, 0))
                self.screen.blit(text, (x + 20, y + 245))

        elif self.personal_combat_step == "attacker_offer":
            lines = [
                "The defender declined to propose.",
                "The attacker now has the option.",
                "",
                "One general from each side will duel.",
                "Refusing when challenged: 8% troop loss!",
            ]
            for i, line in enumerate(lines):
                text = small_font.render(line, True, (220, 220, 220))
                self.screen.blit(text, (x + 20, y + 50 + i * 18))

            text = font.render(
                "Attacker: Propose personal combat?", True, (255, 255, 255)
            )
            self.screen.blit(text, (x + 20, y + 150))
            text = small_font.render("[Y] Yes  [N] No", True, (200, 200, 200))
            self.screen.blit(text, (x + 40, y + 175))

        elif self.personal_combat_step == "attacker_select":
            lines = [
                "Attacker has proposed personal combat!",
                "",
                "Select your champion:",
            ]
            for i, line in enumerate(lines):
                text = small_font.render(line, True, (220, 220, 220))
                self.screen.blit(text, (x + 20, y + 50 + i * 18))

            # List available attacker generals
            available = [u for u in self.battle.attacking_units if not u.is_defeated()]
            for i, unit in enumerate(available[:5]):  # Show up to 5
                name = unit.get_officer_name()
                war = unit.get_war_ability()
                text = small_font.render(
                    f"[{i + 1}] {name} (War {war})", True, (200, 200, 200)
                )
                self.screen.blit(text, (x + 40, y + 110 + i * 20))

            if self.personal_combat_attacker_general:
                name = self.personal_combat_attacker_general.get_officer_name()
                war = self.personal_combat_attacker_general.get_war_ability()
                text = font.render(
                    f"Selected: {name} (War {war})", True, (100, 255, 100)
                )
                self.screen.blit(text, (x + 20, y + 220))
                text = small_font.render("Press ENTER to confirm", True, (255, 255, 0))
                self.screen.blit(text, (x + 20, y + 245))

        elif self.personal_combat_step == "attacker_response":
            name = self.personal_combat_defender_general.get_officer_name()
            war = self.personal_combat_defender_general.get_war_ability()
            lines = [
                f"{name} (War {war}) challenges you!",
                "",
                "Will you accept the duel?",
                "Refusing costs 8% of troops from ALL units!",
            ]
            for i, line in enumerate(lines):
                text = small_font.render(line, True, (220, 220, 220))
                self.screen.blit(text, (x + 20, y + 50 + i * 18))

            text = font.render("Attacker: Accept the challenge?", True, (255, 255, 255))
            self.screen.blit(text, (x + 20, y + 150))
            text = small_font.render("[Y] Accept  [N] Refuse", True, (200, 200, 200))
            self.screen.blit(text, (x + 40, y + 175))

        elif self.personal_combat_step == "defender_response":
            name = self.personal_combat_attacker_general.get_officer_name()
            war = self.personal_combat_attacker_general.get_war_ability()
            lines = [
                f"{name} (War {war}) challenges you!",
                "",
                "Will you accept the duel?",
                "Refusing costs 8% of troops from ALL units!",
            ]
            for i, line in enumerate(lines):
                text = small_font.render(line, True, (220, 220, 220))
                self.screen.blit(text, (x + 20, y + 50 + i * 18))

            text = font.render("Defender: Accept the challenge?", True, (255, 255, 255))
            self.screen.blit(text, (x + 20, y + 150))
            text = small_font.render("[Y] Accept  [N] Refuse", True, (200, 200, 200))
            self.screen.blit(text, (x + 40, y + 175))

    def render_wind_direction(self):
        """Render wind direction and weather indicator."""
        import pygame

        font = pygame.font.SysFont(None, 20)

        # Weather color coding (ROTK2 accurate names)
        weather_colors = {
            "sunny": (255, 255, 100),
            "light_clouds": (220, 220, 200),
            "dark_clouds": (150, 150, 150),
            "storm": (100, 100, 200),
        }

        # Show weather
        weather_display = self.weather.replace("_", " ").title()
        weather_text = f"Weather: {weather_display}"
        weather_color = weather_colors.get(self.weather, (200, 200, 200))
        text = font.render(weather_text, True, weather_color)
        self.screen.blit(text, (self.screen.get_width() - 150, 10))

        # Show wind
        if self.wind_direction:
            text = font.render(f"Wind: {self.wind_direction}", True, (200, 200, 255))
        else:
            text = font.render("Wind: Calm", True, (150, 150, 150))
        self.screen.blit(text, (self.screen.get_width() - 150, 30))

    def render_attack_selection(self):
        """Render attack selection menu."""
        import pygame

        # Darken screen slightly
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(100)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Menu box - calculate height based on options
        menu_width = 350
        base_height = 140  # Normal + Charge
        if "simultaneous" in self.attack_options:
            base_height += 35
        if "fire" in self.attack_options:
            base_height += 35
        menu_height = base_height
        x = (self.screen.get_width() - menu_width) // 2
        y = (self.screen.get_height() - menu_height) // 2

        s = pygame.Surface((menu_width, menu_height))
        s.set_alpha(240)
        s.fill((30, 30, 30))
        self.screen.blit(s, (x, y))

        # Border
        pygame.draw.rect(
            self.screen, (200, 200, 200), (x, y, menu_width, menu_height), 2
        )

        font = pygame.font.SysFont(None, 24)
        small_font = pygame.font.SysFont(None, 20)

        # Title
        target_name = self.attack_target.get_officer_name()
        title = font.render(f"Attack {target_name}", True, (255, 255, 100))
        self.screen.blit(title, (x + 20, y + 15))

        # Attack options
        options = [
            ("1", "Normal Attack", "Standard damage to both sides"),
            ("2", "Charge Attack", "Heavy damage, risky, may pass through"),
        ]

        if "simultaneous" in self.attack_options:
            ally_count = len(self.helping_allies)
            options.append(
                ("3", f"Simultaneous ({ally_count} ally)", "Allies attack together")
            )

        if "fire" in self.attack_options:
            options.append(
                (
                    "4",
                    "Fire Attack",
                    f"Set hex on fire (Int: {self.selected_unit.get_intelligence()})",
                )
            )

        for i, (key, name, desc) in enumerate(options):
            opt_y = y + 50 + i * 35

            # Key
            key_text = small_font.render(f"[{key}]", True, (100, 255, 100))
            self.screen.blit(key_text, (x + 20, opt_y))

            # Name
            name_text = font.render(name, True, (255, 255, 255))
            self.screen.blit(name_text, (x + 60, opt_y))

            # Description
            desc_text = small_font.render(desc, True, (180, 180, 180))
            self.screen.blit(desc_text, (x + 60, opt_y + 18))

        # Cancel instruction
        cancel_text = small_font.render("[ESC] Cancel", True, (200, 200, 200))
        self.screen.blit(cancel_text, (x + 20, y + menu_height - 25))

    def render_end_screen(self):
        """Render battle ended screen."""
        s = pygame.Surface((400, 200))
        s.set_alpha(230)
        s.fill((0, 0, 0))
        x = (self.screen.get_width() - 400) // 2
        y = (self.screen.get_height() - 200) // 2
        self.screen.blit(s, (x, y))

        font = pygame.font.SysFont(None, 36)
        text = font.render("BATTLE ENDED", True, (255, 255, 0))
        self.screen.blit(text, (x + 100, y + 50))

        font = pygame.font.SysFont(None, 24)
        text = font.render("Press ESC to exit", True, (200, 200, 200))
        self.screen.blit(text, (x + 130, y + 120))

    def run(self):
        """Main game loop."""
        print("\n=== BATTLE TEST ===")
        print("Left click: Place units / Select & Move")
        print("SPACE: Auto-place units")
        print("ENTER: Start battle / End turn")
        print("ESC: Exit")
        print("===================\n")

        while self.running:
            self.handle_events()
            self.update()
            self.render()
            self.clock.tick(60)

        pygame.quit()

    def render_combat_markers(self):
        """Render markers for attackable enemies."""
        import pygame

        # Draw red X on adjacent enemies
        for enemy in self.adjacent_enemies:
            if enemy.position:
                cx, cy = self.renderer.hex_to_pixel(enemy.position)
                # Draw X
                pygame.draw.line(
                    self.screen, (255, 0, 0), (cx - 8, cy - 8), (cx + 8, cy + 8), 3
                )
                pygame.draw.line(
                    self.screen, (255, 0, 0), (cx + 8, cy - 8), (cx - 8, cy + 8), 3
                )
                # Draw circle around
                pygame.draw.circle(self.screen, (255, 0, 0), (cx, cy), 15, 2)

    def render_combat_log(self):
        """Render recent combat messages."""
        import pygame

        # Show last 5 combat messages
        y = 150
        font = pygame.font.SysFont(None, 18)

        # Semi-transparent background
        s = pygame.Surface((350, 120))
        s.set_alpha(180)
        s.fill((0, 0, 0))
        self.screen.blit(s, (10, y - 10))

        # Title
        title = font.render("Combat Log:", True, (255, 255, 100))
        self.screen.blit(title, (15, y - 5))

        # Messages
        for i, msg in enumerate(self.combat_log[-5:]):
            text = font.render(msg, True, (200, 200, 200))
            self.screen.blit(text, (15, y + 15 + i * 18))


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
