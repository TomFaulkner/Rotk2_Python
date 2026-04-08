"""
Battle Game - Main game controller for battles.

This module provides the main game loop and input handling for battles,
separate from test-specific setup.
"""

from typing import Optional
from enum import Enum


class BattleGamePhase(Enum):
    """Phases of battle gameplay."""

    PLACEMENT = "placement"
    PERSONAL_COMBAT_OFFER = "personal_combat_offer"
    PERSONAL_COMBAT_SELECT = "personal_combat_select"
    BRIBE_SELECT = "bribe_select"
    REINFORCEMENT_SELECT = "reinforcement_select"
    REINFORCEMENT_PLACEMENT = "reinforcement_placement"
    ATTACK_DIRECTION = "attack_direction"
    BATTLE = "battle"
    ENDED = "ended"


class BattleGame:
    """
    Main battle game controller.

    Handles:
    - Game loop and input processing
    - Phase management
    - Player actions (move, attack, etc.)
    - Personal combat flow

    Uses BattleEngine for game logic and BattleUI for rendering.
    """

    def __init__(self, screen, battle_engine, renderer, cheats: bool = False):
        """
        Initialize battle game.

        Args:
            screen: Pygame surface
            battle_engine: BattleEngine instance
            renderer: BattleRenderer instance
            cheats: Enable debug/cheat features (W for wind, E for weather)
        """
        from Battle import BattleUI, BattlePhaseUI
        from Battle.battle_unit import UnitState
        from Battle.combat_system import CombatSystem

        self.UnitState = UnitState
        self.CombatSystem = CombatSystem

        self.screen = screen
        self.battle = battle_engine
        self.ui = BattleUI(screen, battle_engine, renderer)

        # Game state
        self.running = True
        self.phase = BattleGamePhase.PLACEMENT
        self.ui.set_phase(BattlePhaseUI.PLACEMENT)
        self.placement_side = "attacker"
        self.ui.placement_side = self.placement_side
        self.ui.update_valid_placement_zones()

        # Personal combat state
        self.personal_combat_step = "defender_offer"
        self.personal_combat_defender_general = None
        self.personal_combat_attacker_general = None
        self.personal_combat_proposer = None

        # Bribe state
        self.bribe_target = None
        self.bribe_amount = 0
        self.bribe_step = "select_target"  # select_target, enter_amount, confirm

        # Reinforcement state
        self.reinforcement_overlay = None
        self.reinforcement_unit = None  # Unit being placed
        self.reinforcement_units = []  # Units selected for reinforcement
        self.reinforcement_valid_hexes = []  # Valid placement hexes

        # Attack direction state
        self.attack_direction_target = None  # HexCoord being attacked

        # Cheat/debug mode
        self.cheats = cheats

        print("\n=== BATTLE STARTED ===")
        if cheats:
            print("CHEATS ENABLED: W=cycle wind, E=force weather")
        print("Defender places commander, Attacker places all units")
        print("Controls: Click to place, SPACE to auto-place, ENTER to start")

    def handle_events(self):
        """Process input events."""
        import pygame
        from pygame.locals import (
            QUIT,
            KEYDOWN,
            MOUSEBUTTONDOWN,
            K_ESCAPE,
            K_RETURN,
            K_SPACE,
            K_a,
            K_r,
            K_f,
            K_b,
        )

        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False

            elif event.type == KEYDOWN:
                # Cheat keys (work in any phase)
                if self.cheats:
                    if self._handle_cheat_keys(event.key):
                        continue  # Cheat key was handled, skip other handlers

                if self.phase == BattleGamePhase.REINFORCEMENT_SELECT:
                    self._handle_reinforcement_key(event.key)
                elif self.phase == BattleGamePhase.REINFORCEMENT_PLACEMENT:
                    if event.key == K_ESCAPE:
                        self._cancel_reinforcement_placement()
                    elif event.key == K_SPACE:
                        self._auto_place_reinforcement()
                elif self.phase == BattleGamePhase.ATTACK_DIRECTION:
                    if event.key == K_ESCAPE:
                        self._cancel_attack_direction()
                elif event.key == K_ESCAPE:
                    self._handle_escape()
                elif event.key == K_a:
                    self._enter_attack_direction_mode()
                elif event.key == K_r:
                    if self._can_call_reinforcements():
                        self._start_reinforcement()
                    else:
                        print(
                            "Cannot call reinforcements now (need: defender's turn, reserves available, space on field)"
                        )
                elif (
                    self.phase == BattleGamePhase.PERSONAL_COMBAT_OFFER
                    or self.phase == BattleGamePhase.PERSONAL_COMBAT_SELECT
                ):
                    self._handle_personal_combat_key(event.key)
                elif self.phase == BattleGamePhase.BRIBE_SELECT:
                    self._handle_bribe_key(event.key)
                elif self.ui.attack_target:
                    self._handle_attack_key(event.key)
                elif event.key == K_f:
                    self._toggle_fire_mode()
                elif event.key == K_b:
                    self._toggle_bribe_mode()
                elif event.key == K_SPACE:
                    self._advance_placement()
                elif event.key == K_RETURN:
                    self._handle_return()

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    self._handle_click(event.pos)

    def _handle_escape(self):
        """Handle escape key."""
        if self.ui.attack_target:
            self.ui.attack_target = None
            self.ui.attack_options = []
            print("Attack cancelled")
        else:
            self.running = False

    def _handle_cheat_keys(self, key) -> bool:
        """
        Handle cheat/debug keys.

        Args:
            key: Pygame key constant

        Returns:
            True if a cheat key was handled, False otherwise
        """
        from pygame.locals import K_w, K_e

        if key == K_w:
            # Cycle wind direction
            directions = [None, "N", "NE", "SE", "S", "SW", "NW"]
            current_idx = (
                directions.index(self.battle.wind_direction)
                if self.battle.wind_direction in directions
                else -1
            )
            self.battle.wind_direction = directions[(current_idx + 1) % len(directions)]
            print(f"[CHEAT] Wind: {self.battle.wind_direction or 'Calm'}")
            return True

        elif key == K_e:
            # Force weather transition
            old_weather = self.battle.weather
            new_weather = self.battle.transition_weather()
            print(f"[CHEAT] Weather: {old_weather} -> {new_weather}")
            return True

        return False

    def _handle_return(self):
        """Handle return key."""
        if self.phase == BattleGamePhase.PLACEMENT:
            self._try_start_battle()
        elif self.phase == BattleGamePhase.BATTLE:
            self._end_turn()

    def _handle_personal_combat_key(self, key):
        """Handle keys during personal combat phase."""
        from pygame.locals import (
            K_y,
            K_n,
            K_0,
            K_1,
            K_2,
            K_3,
            K_4,
            K_5,
            K_6,
            K_7,
            K_8,
            K_9,
            K_RETURN,
        )

        if self.personal_combat_step == "defender_offer":
            if key == K_y:
                self.personal_combat_proposer = "defender"
                self.personal_combat_step = "defender_select"
                self.phase = BattleGamePhase.PERSONAL_COMBAT_SELECT
                print("\nDefender proposes personal combat!")
                print("Click a deployed unit or press 1-9,0 to select")
            elif key == K_n:
                self.personal_combat_step = "attacker_offer"
                print("\nDefender declines.")

        elif self.personal_combat_step == "attacker_offer":
            if key == K_y:
                self.personal_combat_proposer = "attacker"
                self.personal_combat_step = "attacker_select"
                self.phase = BattleGamePhase.PERSONAL_COMBAT_SELECT
                print("\nAttacker proposes personal combat!")
                print("Click a deployed unit or press 1-9,0 to select")
            elif key == K_n:
                print("\nBoth declined. Starting battle...")
                self._start_tactical_battle()

        elif self.personal_combat_step == "attacker_response":
            if key == K_y:
                self.personal_combat_step = "attacker_select"
                self.phase = BattleGamePhase.PERSONAL_COMBAT_SELECT
                print("\nAttacker accepts! Select general...")
            elif key == K_n:
                print("\nAttacker refuses! 8% troop loss.")
                result = self.CombatSystem.apply_refuse_penalty_to_side(
                    self.battle.attacking_units, "Attacker"
                )
                print(f"  {result['total_deserted']} troops deserted")
                self._start_tactical_battle()

        elif self.personal_combat_step == "defender_response":
            if key == K_y:
                self.personal_combat_step = "defender_select"
                self.phase = BattleGamePhase.PERSONAL_COMBAT_SELECT
                print("\nDefender accepts! Select general...")
            elif key == K_n:
                print("\nDefender refuses! 8% troop loss.")
                result = self.CombatSystem.apply_refuse_penalty_to_side(
                    self.battle.defending_units, "Defender"
                )
                print(f"  {result['total_deserted']} troops deserted")
                self._start_tactical_battle()

        elif self.personal_combat_step in ["defender_select", "attacker_select"]:
            # Map keys 1-9,0 to indices 0-9 (0 key = 10th unit)
            key_to_idx = {
                K_1: 0,
                K_2: 1,
                K_3: 2,
                K_4: 3,
                K_5: 4,
                K_6: 5,
                K_7: 6,
                K_8: 7,
                K_9: 8,
                K_0: 9,
            }
            if key in key_to_idx:
                idx = key_to_idx[key]
                if self.personal_combat_step == "defender_select":
                    available = [
                        u
                        for u in self.battle.defending_units
                        if not u.is_defeated() and u.position
                    ]
                else:
                    available = [
                        u
                        for u in self.battle.attacking_units
                        if not u.is_defeated() and u.position
                    ]

                if idx < len(available):
                    self._select_general_for_duel(available[idx])
            elif key == K_RETURN:
                if (
                    self.personal_combat_defender_general
                    and self.personal_combat_attacker_general
                ):
                    self._resolve_duel()

    def _handle_attack_key(self, key):
        """Handle keys during attack selection."""
        from pygame.locals import (
            K_1,
            K_2,
            K_3,
            K_4,
            K_KP1,
            K_KP2,
            K_KP3,
            K_KP4,
            K_ESCAPE,
        )

        if key == K_ESCAPE:
            self.ui.attack_target = None
            self.ui.attack_options = []
            print("Attack cancelled")
        elif key in [K_1, K_KP1]:
            self._execute_attack("normal")
        elif key in [K_2, K_KP2]:
            self._execute_attack("charge")
        elif key in [K_3, K_KP3]:
            if "simultaneous" in self.ui.attack_options:
                self._execute_attack("simultaneous")
        elif key in [K_4, K_KP4]:
            if "fire" in self.ui.attack_options:
                self.ui.fire_mode = True
                self.ui.attack_target = None
                self.ui.attack_options = []
                print("Fire mode: Click adjacent hex")

    def _handle_reinforcement_key(self, key):
        """Handle keys during reinforcement selection."""
        from pygame.locals import (
            K_ESCAPE,
            K_UP,
            K_DOWN,
            K_RETURN,
            K_1,
            K_2,
            K_3,
            K_4,
            K_5,
            K_6,
            K_7,
            K_8,
            K_9,
            K_0,
        )

        if self.reinforcement_overlay is None:
            self.phase = BattleGamePhase.BATTLE
            return

        # Handle navigation keys
        if key == K_ESCAPE:
            # Cancel reinforcement
            self.reinforcement_overlay = None
            self.phase = BattleGamePhase.BATTLE
            print("Reinforcement cancelled")
        elif key == K_UP:
            self.reinforcement_overlay.selected_index = max(
                0, self.reinforcement_overlay.selected_index - 1
            )
            self.reinforcement_overlay._ensure_visible()
        elif key == K_DOWN:
            max_idx = len(self.reinforcement_overlay.items) - 1
            self.reinforcement_overlay.selected_index = min(
                max_idx, self.reinforcement_overlay.selected_index + 1
            )
            self.reinforcement_overlay._ensure_visible()
        elif key == K_RETURN:
            # Confirm selection
            self._handle_reinforcement_selection()
        elif key in (K_1, K_2, K_3, K_4, K_5, K_6, K_7, K_8, K_9):
            # Number key selection
            visible_idx = key - K_1  # 0-8
            actual_idx = self.reinforcement_overlay.scroll_offset + visible_idx
            if actual_idx < len(self.reinforcement_overlay.items):
                self.reinforcement_overlay.selected_index = actual_idx
                self._handle_reinforcement_selection()
        elif key == K_0:
            # 0 key selects 10th visible item
            actual_idx = self.reinforcement_overlay.scroll_offset + 9
            if actual_idx < len(self.reinforcement_overlay.items):
                self.reinforcement_overlay.selected_index = actual_idx
                self._handle_reinforcement_selection()

    def _handle_bribe_key(self, key):
        """Handle keys during bribe modal."""
        from pygame.locals import (
            K_0,
            K_1,
            K_2,
            K_3,
            K_4,
            K_5,
            K_6,
            K_7,
            K_8,
            K_9,
            K_BACKSPACE,
            K_ESCAPE,
            K_y,
            K_n,
        )

        if self.bribe_step == "select_target":
            # Map keys 1-9,0 to target selection
            key_to_idx = {
                K_1: 0,
                K_2: 1,
                K_3: 2,
                K_4: 3,
                K_5: 4,
                K_6: 5,
                K_7: 6,
                K_8: 7,
                K_9: 8,
                K_0: 9,
            }
            if key in key_to_idx:
                idx = key_to_idx[key]
                # Get enemy units
                if self.ui.selected_unit.is_attacker:
                    enemies = [
                        u
                        for u in self.battle.defending_units
                        if not u.is_defeated() and u.position
                    ]
                else:
                    enemies = [
                        u
                        for u in self.battle.attacking_units
                        if not u.is_defeated() and u.position
                    ]

                if idx < len(enemies):
                    self.bribe_target = enemies[idx]
                    self.bribe_step = "enter_amount"
                    self.bribe_amount = 0
                    print(f"\nTarget: {self.bribe_target.get_officer_name()}")
                    print(
                        "Enter bribe amount (1-99), then press Y to confirm or N to cancel"
                    )

        elif self.bribe_step == "enter_amount":
            if K_0 <= key <= K_9:
                digit = key - K_0
                self.bribe_amount = self.bribe_amount * 10 + digit
                if self.bribe_amount > 99:
                    self.bribe_amount = 99
                print(f"  Amount: {self.bribe_amount} gold")
            elif key == K_BACKSPACE:
                self.bribe_amount = self.bribe_amount // 10
                print(f"  Amount: {self.bribe_amount} gold")
            elif key == K_y:
                if self.bribe_amount >= 1:
                    self._execute_bribe()
                else:
                    print("Enter amount first!")
            elif key == K_n:
                self._cancel_bribe()

        elif key == K_ESCAPE:
            self._cancel_bribe()

    def _cancel_bribe(self):
        """Cancel bribe mode."""
        self.phase = BattleGamePhase.BATTLE
        self.bribe_target = None
        self.bribe_amount = 0
        self.bribe_step = "select_target"
        print("Bribe cancelled")

    # ==================== REINFORCEMENT SYSTEM ====================

    def _can_call_reinforcements(self) -> bool:
        """
        Check if defender can call reinforcements.

        Returns:
            True if reinforcements are available and defender has space
        """
        # Only defender can reinforce during their turn
        if self.battle.turn != 1:  # 1 = defender's turn
            return False

        # Check if there are available reserves
        available_reserves = self.battle.defender_reserve.get_available()
        if not available_reserves:
            return False

        # Check active unit count (excluding defeated, captured, retreated, injured)
        active_count = self._get_active_defender_count()
        if active_count >= self.battle.MAX_UNITS_ON_MAP:
            return False

        return True

    def _get_active_defender_count(self) -> int:
        """
        Get count of active defending units on the battlefield.

        Excludes: DEFEATED, CAPTURED, RETREATED, INJURED
        """
        exclude_states = {
            self.UnitState.DEFEATED,
            self.UnitState.CAPTURED,
            self.UnitState.RETREATED,
            self.UnitState.INJURED,
        }

        count = 0
        for unit in self.battle.defending_units:
            if unit.state not in exclude_states and unit.position is not None:
                count += 1
        return count

    def _start_reinforcement(self):
        """Start the reinforcement selection process."""
        from Battle.battle_ui import ScrollableListOverlay

        available_reserves = self.battle.defender_reserve.get_available()
        if not available_reserves:
            print("No reinforcements available")
            return

        # Build item list for scrollable overlay
        items = []
        for unit in available_reserves:
            items.append(
                {
                    "id": unit.get_officer_id(),
                    "name": unit.get_officer_name(),
                    "stats": f"War:{unit.get_war_ability()} Int:{unit.get_intelligence()} Sol:{unit.soldiers}",
                    "unit": unit,
                }
            )

        self.reinforcement_overlay = ScrollableListOverlay(
            screen=self.screen,
            items=items,
            title=f"Call Reinforcements ({len(available_reserves)} available)",
            visible_count=10,
            border_color=(100, 150, 255),  # Blue border for reinforcements
        )

        self.phase = BattleGamePhase.REINFORCEMENT_SELECT
        print(
            "Select a reinforcement (1-9,0 or navigate with arrows, Enter to confirm)"
        )

    def _handle_reinforcement_selection(self):
        """Handle reinforcement selection from overlay."""
        if self.reinforcement_overlay is None:
            self.phase = BattleGamePhase.BATTLE
            return

        # Get selected item directly from selected_index (not from confirmed_selection)
        selected_idx = self.reinforcement_overlay.selected_index
        if selected_idx < 0 or selected_idx >= len(self.reinforcement_overlay.items):
            self.reinforcement_overlay = None
            self.phase = BattleGamePhase.BATTLE
            print("Reinforcement cancelled")
            return

        selection = self.reinforcement_overlay.items[selected_idx]
        self.reinforcement_overlay = None

        unit = selection.get("unit")
        if not unit:
            self.phase = BattleGamePhase.BATTLE
            return

        # Remove from reserve and add to defending units
        self.battle.defender_reserve.remove(unit)
        if unit not in self.battle.defending_units:
            self.battle.defending_units.append(unit)

        unit.state = self.UnitState.INACTIVE  # Ready for placement
        self.reinforcement_unit = unit
        self.reinforcement_units = [unit]

        # Calculate valid placement hexes
        self.reinforcement_valid_hexes = self._get_reinforcement_placement_hexes()

        if not self.reinforcement_valid_hexes:
            print("No valid placement positions available!")
            unit.state = self.UnitState.IN_RESERVE
            self.battle.defender_reserve.add(unit)
            self.phase = BattleGamePhase.BATTLE
            return

        self.phase = BattleGamePhase.REINFORCEMENT_PLACEMENT
        print(f"Place {unit.get_officer_name()} on the battlefield")
        print(f"Valid hexes: {len(self.reinforcement_valid_hexes)}")

    def _get_reinforcement_placement_hexes(self) -> list:
        """
        Get valid hexes for placing reinforcements.

        Uses defender placement zones minus occupied hexes.
        """
        # Get base defender zones
        base_hexes = self.battle._get_defender_placement_zones()

        # Filter out occupied hexes
        valid_hexes = []
        for coord in base_hexes:
            hex_obj = self.battle.grid.get_hex(coord)
            if hex_obj and hex_obj.is_passable() and hex_obj.unit is None:
                valid_hexes.append(coord)

        return valid_hexes

    def _handle_reinforcement_placement_click(self, coord):
        """Handle click during reinforcement placement."""
        if self.reinforcement_unit is None:
            return
        if coord not in self.reinforcement_valid_hexes:
            print("Invalid placement position")
            return

        if self.battle.place_unit(self.reinforcement_unit, coord):
            print(
                f"Reinforcement {self.reinforcement_unit.get_officer_name()} placed at {coord}"
            )
            self.ui.add_combat_message(
                f"Reinforcement: {self.reinforcement_unit.get_officer_name()}"
            )

            # Auto-hide if placed in forest
            hex_obj = self.battle.grid.get_hex(coord)
            if hex_obj and hex_obj.terrain.name.lower() == "forest":
                self.reinforcement_unit.hide()
                print(
                    f"{self.reinforcement_unit.get_officer_name()} is hidden in the forest"
                )

            # Continue with reinforcements or return to battle
            self._continue_or_end_reinforcement()

    def _auto_place_reinforcement(self):
        """Auto-place reinforcement in a valid position."""
        if self.reinforcement_unit is None:
            return
        if not self.reinforcement_valid_hexes:
            print("No valid positions for auto-placement")
            self._cancel_reinforcement_placement()
            return

        # Pick first available hex
        coord = self.reinforcement_valid_hexes[0]
        self._handle_reinforcement_placement_click(coord)

    def _cancel_reinforcement_placement(self):
        """Cancel reinforcement placement and return unit to reserve."""
        if self.reinforcement_unit:
            # Return unit to reserve
            self.reinforcement_unit.state = self.UnitState.IN_RESERVE
            if self.reinforcement_unit not in [
                u for u in self.battle.defender_reserve.units
            ]:
                self.battle.defender_reserve.add(self.reinforcement_unit)
            print(f"{self.reinforcement_unit.get_officer_name()} returned to reserve")

        self.reinforcement_unit = None
        self.reinforcement_units = []
        self.reinforcement_valid_hexes = []
        self.phase = BattleGamePhase.BATTLE

    def _continue_or_end_reinforcement(self):
        """Check if more reinforcements can be called or return to battle."""
        self.reinforcement_unit = None
        self.reinforcement_units = []
        self.reinforcement_valid_hexes = []

        # Check if defender can call more reinforcements
        if self._can_call_reinforcements():
            # Ask if they want to call another
            print("Press R to call another reinforcement, or continue with battle")
            # Return to battle phase but they'll be able to press R again
            self.phase = BattleGamePhase.BATTLE
        else:
            self.phase = BattleGamePhase.BATTLE

    # ==================== ATTACK DIRECTION SYSTEM ====================

    def _enter_attack_direction_mode(self):
        """Enter attack direction mode to attack any adjacent hex."""
        if not self.ui.selected_unit:
            print("Select a unit first")
            return

        unit = self.ui.selected_unit
        if not unit.can_attack():
            print("Selected unit cannot attack")
            return

        # Get adjacent hexes
        adjacent_hexes = self.battle.grid.get_adjacent(unit.position)
        if not adjacent_hexes:
            print("No adjacent hexes to attack")
            return

        self.attack_direction_target = None
        self.phase = BattleGamePhase.ATTACK_DIRECTION
        print("ATTACK DIRECTION MODE: Click an adjacent hex to attack")
        print("(Hidden units will take damage but stay hidden)")

    def _cancel_attack_direction(self):
        """Cancel attack direction mode."""
        self.attack_direction_target = None
        self.phase = BattleGamePhase.BATTLE
        print("Attack direction cancelled")

    def _handle_attack_direction_click(self, coord):
        """Handle click during attack direction mode."""
        unit = self.ui.selected_unit
        if not unit:
            self._cancel_attack_direction()
            return

        # Check if clicked hex is adjacent
        adjacent_hexes = self.battle.grid.get_adjacent(unit.position)
        if coord not in adjacent_hexes:
            print("Can only attack adjacent hexes")
            return

        # Check if there's a visible enemy at this hex
        hex_obj = self.battle.grid.get_hex(coord)
        if hex_obj and hex_obj.unit:
            target = hex_obj.unit
            if target.is_attacker != unit.is_attacker and not target.is_defeated():
                # Attack visible enemy
                self._execute_directional_attack(coord, target)
                return

        # Check for hidden enemies at this hex
        all_units = self.battle.get_all_units_on_map()
        hidden_enemy = None
        for u in all_units:
            if (
                u.is_attacker != unit.is_attacker
                and u.is_hidden()
                and not u.is_defeated()
                and u.position == coord
            ):
                hidden_enemy = u
                break

        if hidden_enemy:
            # Attack hidden enemy - they take damage but stay hidden
            self._execute_directional_attack(coord, hidden_enemy, is_hidden_target=True)
        else:
            # Attack empty hex
            print(f"Attacking empty hex {coord}")
            self._execute_directional_attack(coord, None)

    def _execute_directional_attack(self, coord, target, is_hidden_target=False):
        """Execute attack on a specific hex/direction."""
        unit = self.ui.selected_unit

        if target and not target.is_defeated():
            # Perform normal attack
            result = self.CombatSystem.calculate_normal_attack(
                unit, target, self.battle.grid
            )

            # Apply damage
            if result.defender_casualties > 0:
                if is_hidden_target:
                    print(
                        f"HIT! Hidden unit at {coord} takes {result.defender_casualties} damage!"
                    )
                    self.ui.add_combat_message(
                        f"Hit hidden unit for {result.defender_casualties} damage!"
                    )
                else:
                    print(
                        f"Hit {target.get_officer_name()} for {result.defender_casualties} damage"
                    )
                    self.ui.add_combat_message(
                        f"Hit {target.get_officer_name()} for {result.defender_casualties} damage"
                    )

            # Hidden units stay hidden even when hit
            # They only get revealed if they ambush or if the player remembers

            # Check if target defeated
            if result.defender_defeated:
                if is_hidden_target:
                    # Hidden unit defeated - now we reveal them
                    target.state = self.UnitState.DEFEATED
                    print(f"Hidden unit at {coord} has been defeated!")
                    self.ui.add_combat_message("Hidden unit defeated!")
                else:
                    print(f"{target.get_officer_name()} defeated!")
                    self.ui.add_combat_message(f"{target.get_officer_name()} defeated!")

                # Remove from grid
                if target.position:
                    self.battle.grid.remove_unit(target.position)
        else:
            # No target - attack misses
            print(f"Attack on {coord} finds no target")
            self.ui.add_combat_message("Attack missed - no target")

        # Mark unit as having attacked
        unit.has_attacked = True
        unit.state = self.UnitState.ATTACKED

        # Clear selection and return to battle
        self.ui.clear_selection()
        self.attack_direction_target = None
        self.phase = BattleGamePhase.BATTLE

    def _handle_click(self, pos):
        """Handle mouse click."""
        x, y = pos
        clicked_hex = self.ui.get_hex_at_pixel(x, y)
        if not clicked_hex:
            return

        if self.phase == BattleGamePhase.PLACEMENT:
            self._handle_placement_click(clicked_hex)
        elif self.phase == BattleGamePhase.PERSONAL_COMBAT_SELECT:
            self._handle_personal_combat_click(clicked_hex)
        elif self.phase == BattleGamePhase.REINFORCEMENT_PLACEMENT:
            self._handle_reinforcement_placement_click(clicked_hex)
        elif self.phase == BattleGamePhase.ATTACK_DIRECTION:
            self._handle_attack_direction_click(clicked_hex)
        elif self.phase == BattleGamePhase.BATTLE:
            self._handle_battle_click(clicked_hex)

    def _handle_placement_click(self, coord):
        """Handle click during placement."""
        is_attacker = self.placement_side == "attacker"

        if not self.battle.is_valid_placement(coord, is_attacker):
            hex_obj = self.battle.grid.get_hex(coord)
            if hex_obj:
                print(
                    f"DEBUG INVALID PLACEMENT: {coord}, terrain={hex_obj.terrain.name}, passable={hex_obj.is_passable()}, is_castle={hex_obj.is_castle}"
                )
            else:
                print(f"DEBUG INVALID PLACEMENT: {coord}, no hex found")
            print("Invalid placement zone")
            return

        # Get next unplaced unit
        if is_attacker:
            unplaced = [
                u
                for u in self.battle.attacking_units
                if u.state == self.UnitState.INACTIVE
            ]
        else:
            unplaced = [
                u
                for u in self.battle.defending_units
                if u.state == self.UnitState.INACTIVE
            ]

        if not unplaced:
            return

        unit = unplaced[0]
        if self.battle.place_unit(unit, coord):
            print(f"Placed {unit.get_officer_name()} at {coord}")
            self.ui.add_combat_message(f"Placed {unit.get_officer_name()}")

            # Auto-hide unit if placed in forest
            hex_obj = self.battle.grid.get_hex(coord)
            if hex_obj and hex_obj.terrain.name.lower() == "forest":
                unit.hide()
                print(f"{unit.get_officer_name()} is hidden in the forest")

            # Check if side is done
            if is_attacker:
                remaining = [
                    u
                    for u in self.battle.attacking_units
                    if u.state == self.UnitState.INACTIVE
                ]
                if not remaining:
                    self.placement_side = "defender"
                    self.ui.placement_side = "defender"
                    self.ui.update_valid_placement_zones()
                    print("\nDefender's turn to place units")
            else:
                remaining = [
                    u
                    for u in self.battle.defending_units
                    if u.state == self.UnitState.INACTIVE
                ]
                if not remaining:
                    print("\nAll units placed! Press ENTER to start battle")

    def _handle_personal_combat_click(self, coord):
        """Handle click during personal combat general selection."""
        hex_obj = self.battle.grid.get_hex(coord)
        if not hex_obj or not hex_obj.unit:
            return

        unit = hex_obj.unit

        if self.personal_combat_step == "defender_select":
            if unit in self.battle.defending_units and not unit.is_defeated():
                self._select_general_for_duel(unit)
        elif self.personal_combat_step == "attacker_select":
            if unit in self.battle.attacking_units and not unit.is_defeated():
                self._select_general_for_duel(unit)

    def _handle_battle_click(self, coord):
        """Handle click during battle."""
        # Fire mode
        if self.ui.fire_mode and self.ui.selected_unit:
            # TODO: Implement fire attack
            print("Fire attack not fully implemented")
            self.ui.fire_mode = False
            return

        hex_obj = self.battle.grid.get_hex(coord)

        if hex_obj and hex_obj.unit:
            unit = hex_obj.unit

            # Attack enemy
            if (
                self.ui.selected_unit
                and unit.is_attacker != self.ui.selected_unit.is_attacker
                and not unit.is_defeated()
            ):
                if unit in self.ui.adjacent_enemies:
                    self._start_attack_selection(unit)
                    return

            # Select unit
            self.ui.selected_unit = unit
            self.ui.reachable_hexes = []
            self.ui.adjacent_enemies = []

            if unit.can_move():
                self.ui.reachable_hexes = self.battle.grid.get_movement_range(
                    coord, unit.mobility
                )
                # Debug: count mountain hexes that would be reachable if not blocked
                mountain_count = 0
                for check_coord in self.ui.reachable_hexes:
                    check_hex = self.battle.grid.get_hex(check_coord)
                    if check_hex and check_hex.terrain.name.lower() == "mountain":
                        mountain_count += 1
                if mountain_count > 0:
                    print(
                        f"  Warning: {mountain_count} mountain hexes in reachable_hexes!"
                    )

            all_units = self.battle.get_all_units_on_map()
            self.ui.adjacent_enemies = self.CombatSystem.get_adjacent_enemies(
                unit, self.battle.grid, all_units
            )

            # Get terrain type and hidden state for display
            terrain_name = "Unknown"
            hidden_status = ""
            if unit.position:
                hex_obj = self.battle.grid.get_hex(unit.position)
                if hex_obj:
                    terrain_name = hex_obj.terrain.name
                if unit.is_hidden():
                    hidden_status = ", HIDDEN"

            print(
                f"Selected: {unit.get_officer_name()}, mobility: {unit.mobility}, reachable: {len(self.ui.reachable_hexes)}, terrain: {terrain_name}{hidden_status}"
            )

        elif self.ui.selected_unit and self.ui.selected_unit.can_move():
            # Check if the clicked hex is adjacent to current position (step-by-step movement)
            if self.ui.selected_unit.position:
                adjacent_coords = self.battle.grid.get_adjacent(
                    self.ui.selected_unit.position
                )
                is_adjacent = coord in adjacent_coords
            else:
                is_adjacent = False

            # Check if unit can afford the movement cost
            if hex_obj:
                move_cost = hex_obj.get_movement_cost()
                if self.ui.selected_unit.mobility < move_cost:
                    print(
                        f"Not enough mobility! Need {move_cost}, have {self.ui.selected_unit.mobility}"
                    )
                    return

            # For multi-tile moves, check if we'd pass adjacent to enemies
            if not is_adjacent and coord in self.ui.reachable_hexes:
                # Check if destination is adjacent to enemy - if so, only allow single-step
                friendly_units = (
                    self.battle.get_attacking_units_on_map()
                    if self.ui.selected_unit.is_attacker
                    else self.battle.get_defending_units_on_map()
                )
                if self.battle.grid.is_adjacent_to_enemy(coord, friendly_units):
                    print(
                        "Cannot move directly to hex adjacent to enemy. Move one step at a time."
                    )
                    return

            # Allow move if adjacent OR if in reachable_hexes (for longer moves)
            if is_adjacent or coord in self.ui.reachable_hexes:
                self._execute_move(coord)
            else:
                # Log invalid tile selection
                if hex_obj:
                    print(
                        f"DEBUG INVALID CLICK: Clicked {coord}, terrain={hex_obj.terrain.name}, passable={hex_obj.is_passable()}"
                    )
                else:
                    print(f"DEBUG INVALID CLICK: Clicked {coord}, no hex found")

    def _select_general_for_duel(self, unit):
        """Select a general for personal combat."""
        if not unit or unit.is_defeated() or not unit.position:
            print("Invalid unit selection")
            return

        if self.personal_combat_step == "defender_select":
            self.personal_combat_defender_general = unit
            print(
                f"\nDefender: {unit.get_officer_name()} (War {unit.get_war_ability()})"
            )

            if self.personal_combat_proposer == "defender":
                self.personal_combat_step = "attacker_response"
                self.phase = BattleGamePhase.PERSONAL_COMBAT_OFFER
                print("Attacker: Press Y to accept, N to refuse")
            else:
                self._check_personal_combat_ready()

        elif self.personal_combat_step == "attacker_select":
            self.personal_combat_attacker_general = unit
            print(
                f"\nAttacker: {unit.get_officer_name()} (War {unit.get_war_ability()})"
            )

            if self.personal_combat_proposer == "attacker":
                self.personal_combat_step = "defender_response"
                self.phase = BattleGamePhase.PERSONAL_COMBAT_OFFER
                print("Defender: Press Y to accept, N to refuse")
            else:
                self._check_personal_combat_ready()

    def _check_personal_combat_ready(self):
        """Check if both generals selected."""
        if (
            self.personal_combat_defender_general
            and self.personal_combat_attacker_general
        ):
            self._resolve_duel()

    def _resolve_duel(self):
        """Resolve the personal combat duel."""
        att = self.personal_combat_attacker_general
        defe = self.personal_combat_defender_general

        print(f"\n{'=' * 50}")
        print(f"PERSONAL COMBAT")
        print(f"{att.get_officer_name()} (War {att.get_war_ability()})")
        print(f"  vs")
        print(f"{defe.get_officer_name()} (War {defe.get_war_ability()})")
        print(f"{'=' * 50}")

        result = self.CombatSystem.resolve_personal_combat_with_consequences(
            att, defe, self.battle
        )
        duel = result["duel_result"]

        # Show rounds
        for rd in duel["rounds"]:
            print(
                f"Round {rd['round']}: "
                f"{att.get_officer_name()} HP={rd['att_stamina']} | "
                f"{defe.get_officer_name()} HP={rd['def_stamina']}"
            )

        print(f"\n{duel['message']}")

        if result["commander_captured"]:
            print(f"\n*** {result['captured_side'].upper()} COMMANDER CAPTURED! ***")
            print("All units retreat! Battle over!")
            from Battle import BattlePhaseUI

            self.phase = BattleGamePhase.ENDED
            self.ui.set_phase(BattlePhaseUI.ENDED)
        else:
            print("\nDuel complete. Starting tactical battle...")
            self._start_tactical_battle()

    def _start_attack_selection(self, target):
        """Start attack selection."""
        if not self.ui.selected_unit or not self.ui.selected_unit.can_attack():
            return

        all_units = self.battle.get_all_units_on_map()
        # For simultaneous attacks, find allies adjacent to the TARGET (not the attacker)
        helping_allies = self.CombatSystem.get_allies_adjacent_to_target(
            self.ui.selected_unit, target, self.battle.grid, all_units
        )

        self.ui.helping_allies = helping_allies

        self.ui.attack_target = target
        self.ui.attack_options = ["normal", "charge"]
        if self.ui.helping_allies:
            self.ui.attack_options.append("simultaneous")
        self.ui.attack_options.append("fire")

        print(f"\nAttack {target.get_officer_name()}:")
        print("  [1] Normal Attack")
        print("  [2] Charge Attack")
        if self.ui.helping_allies:
            print(f"  [3] Simultaneous ({len(self.ui.helping_allies)} allies)")
        print("  [4] Fire Attack")
        print("  [ESC] Cancel")

    def _execute_attack(self, attack_type):
        """Execute attack."""
        if not self.ui.selected_unit or not self.ui.selected_unit.can_attack():
            return

        target = self.ui.attack_target

        if attack_type == "fire":
            print("Fire attack - select hex")
            self.ui.fire_mode = True
            self.ui.attack_target = None
            self.ui.attack_options = []
            return

        if attack_type == "simultaneous" and self.ui.helping_allies:
            result = self.CombatSystem.calculate_simultaneous_attack(
                [self.ui.selected_unit] + self.ui.helping_allies,
                target,
                self.battle.grid,
            )
        elif attack_type == "charge":
            result = self.CombatSystem.calculate_charge_attack(
                self.ui.selected_unit, target, self.battle.grid
            )
        else:
            result = self.CombatSystem.calculate_normal_attack(
                self.ui.selected_unit, target, self.battle.grid
            )

        for msg in result.messages:
            print(f"  {msg}")
            self.ui.add_combat_message(msg)

        self.ui.selected_unit.has_attacked = True

        if result.defender_defeated:
            self.battle.grid.remove_unit(target.position)

        if result.attacker_defeated:
            self.battle.grid.remove_unit(self.ui.selected_unit.position)
            self.ui.selected_unit = None

        self.ui.attack_target = None
        self.ui.attack_options = []

        victory = self.battle.check_victory()
        if victory:
            from Battle import BattlePhaseUI

            self.phase = BattleGamePhase.ENDED
            self.ui.set_phase(BattlePhaseUI.ENDED)
            print(f"\n*** BATTLE ENDED: {victory.name} ***")

    def _execute_move(self, coord):
        """Execute unit movement."""
        unit = self.ui.selected_unit

        # Check if destination is passable before attempting move
        hex_obj = self.battle.grid.get_hex(coord)
        if hex_obj:
            print(
                f"DEBUG MOVE: Moving to {coord}, terrain={hex_obj.terrain.name}, passable={hex_obj.is_passable()}"
            )

        if hex_obj and not hex_obj.is_passable():
            print(
                f"BLOCKED: Cannot move to {coord}: terrain is impassable ({hex_obj.terrain.name})"
            )
            return

        if self.battle.grid.place_unit(unit, coord):
            hex_obj = self.battle.grid.get_hex(coord)
            cost = hex_obj.get_movement_cost()
            unit.move_to(coord, cost)

            # Get friendly units to check adjacency against enemies
            friendly_units = (
                self.battle.get_attacking_units_on_map()
                if unit.is_attacker
                else self.battle.get_defending_units_on_map()
            )

            # Check for forest ambush from hidden enemies
            all_units = self.battle.get_all_units_on_map()
            hidden_enemies = self.CombatSystem.get_hidden_enemies_adjacent_to(
                self.battle.grid, coord, all_units, unit.is_attacker
            )

            ambush_triggered = False
            for hidden_enemy in hidden_enemies:
                damage = self.CombatSystem.perform_forest_ambush(
                    hidden_enemy, unit, self.battle.grid
                )
                if damage > 0:
                    ambush_triggered = True

            if ambush_triggered:
                # Check if unit should hide in forest after ambush
                if hex_obj.terrain.name.lower() == "forest":
                    unit.hide()
                    print(f"{unit.get_officer_name()} hides in the forest after ambush")
                else:
                    unit.engage()
                print(f"Ambushed! {unit.get_officer_name()} turn ends")
                self.ui.clear_selection()
                return

            if self.battle.grid.is_adjacent_to_enemy(coord, friendly_units):
                unit.engage()
                print(f"Engaged enemy! {unit.get_officer_name()} turn ends")
                self.ui.reachable_hexes = []
            elif not unit.can_move():
                # Unit has no more mobility, clear reachable hexes
                self.ui.reachable_hexes = []
            else:
                # Unit can still move, update reachable hexes from new position
                self.ui.reachable_hexes = self.battle.grid.get_movement_range(
                    coord, unit.mobility
                )
                print(
                    f"Remaining mobility: {unit.mobility}, reachable hexes: {len(self.ui.reachable_hexes)}"
                )

            self.ui.adjacent_enemies = self.CombatSystem.get_adjacent_enemies(
                unit, self.battle.grid, all_units
            )

            # Auto-hide unit if in forest
            if hex_obj.terrain.name.lower() == "forest":
                unit.hide()
                print(f"{unit.get_officer_name()} hides in the forest")

    def _execute_bribe(self):
        """Execute bribe with selected target and amount."""
        if not self.bribe_target:
            print("No target selected!")
            return
        if self.bribe_amount < 1:
            print("Enter bribe amount (1-99)")
            return

        briber = self.ui.selected_unit
        if not briber or not briber.is_commander:
            print("Only commander can bribe!")
            self._cancel_bribe()
            return

        target = self.bribe_target
        briber_charm = getattr(briber.officer, "Chm", 50)
        success, roll, defense = self.CombatSystem.calculate_bribe_success(
            briber_charm, target, self.bribe_amount
        )

        print(f"\n=== BRIBE RESULT ===")
        print(f"Target: {target.get_officer_name()}")
        print(f"Amount: {self.bribe_amount} gold")
        print(f"Defense: {defense}  Roll: {roll}")

        if success:
            print(f"SUCCESS! {target.get_officer_name()} defects!")
            target.is_attacker = briber.is_attacker
            self.ui.add_combat_message(f"Bribe: {target.get_officer_name()} defected!")

            # Check if bribed unit was a commander
            if target.is_commander:
                print(f"\n*** ENEMY COMMANDER BRIBED! ***")
                print(">>> ALL ENEMY UNITS FLEE! <<<")

                # Determine which side's commander was bribed
                bribed_side_is_attacker = not briber.is_attacker

                # Force all units on that side to flee
                if bribed_side_is_attacker:
                    units_to_flee = self.battle.get_attacking_units_on_map()
                    for unit in units_to_flee:
                        unit.state = self.UnitState.DEFEATED
                        if unit.position:
                            self.battle.grid.remove_unit(unit.position)
                        print(f"  {unit.get_officer_name()} flees!")
                else:
                    units_to_flee = self.battle.get_defending_units_on_map()
                    for unit in units_to_flee:
                        unit.state = self.UnitState.CAPTURED
                        if unit.position:
                            self.battle.grid.remove_unit(unit.position)
                        print(f"  {unit.get_officer_name()} flees!")

                briber.has_attacked = True
                briber.has_moved = True

                # Exit bribe mode and end battle
                self.phase = BattleGamePhase.ENDED
                from Battle import BattlePhaseUI

                self.ui.set_phase(BattlePhaseUI.ENDED)
                print(f"\n*** BATTLE ENDED: BRIBER WINS ***")
                return
        else:
            print(f"FAILED! {target.get_officer_name()} refuses!")

        briber.has_attacked = True
        briber.has_moved = True

        # Exit bribe mode
        self.phase = BattleGamePhase.BATTLE
        self.bribe_target = None
        self.bribe_amount = 0
        self.bribe_step = "select_target"

    def _toggle_fire_mode(self):
        """Toggle fire attack mode."""
        if self.phase != BattleGamePhase.BATTLE:
            return
        if not self.ui.selected_unit:
            print("Select a unit first")
            return

        self.ui.fire_mode = not self.ui.fire_mode
        if self.ui.fire_mode:
            print("Fire mode: Click adjacent hex")
        else:
            print("Fire mode off")

    def _toggle_bribe_mode(self):
        """Enter bribe mode with modal selection."""
        if self.phase != BattleGamePhase.BATTLE:
            return
        if not self.ui.selected_unit:
            print("Select a unit first")
            return
        if not self.ui.selected_unit.is_commander:
            print("Only commander can bribe!")
            return
        if self.ui.selected_unit.has_attacked or self.ui.selected_unit.has_moved:
            print("Commander has already acted!")
            return

        # Enter bribe selection phase
        self.phase = BattleGamePhase.BRIBE_SELECT
        self.bribe_step = "select_target"
        self.bribe_target = None
        self.bribe_amount = 0
        print("\n=== BRIBE MODE ===")
        print("Select enemy unit to bribe (1-9, 0 for 10th)")

    def _advance_placement(self):
        """Auto-place remaining units."""
        is_attacker = self.placement_side == "attacker"

        if is_attacker:
            unplaced = [
                u
                for u in self.battle.attacking_units
                if u.state == self.UnitState.INACTIVE
            ]
        else:
            unplaced = [
                u
                for u in self.battle.defending_units
                if u.state == self.UnitState.INACTIVE
            ]

        valid_hexes = self.battle.get_valid_placement_hexes(is_attacker)

        for i, unit in enumerate(unplaced):
            if i < len(valid_hexes):
                coord = valid_hexes[i]
                self.battle.place_unit(unit, coord)
                print(f"Auto-placed {unit.get_officer_name()}")

                # Auto-hide unit if placed in forest
                hex_obj = self.battle.grid.get_hex(coord)
                if hex_obj and hex_obj.terrain.name.lower() == "forest":
                    unit.hide()
                    print(f"{unit.get_officer_name()} is hidden in the forest")

        if is_attacker:
            self.placement_side = "defender"
            self.ui.placement_side = "defender"
            self.ui.update_valid_placement_zones()
            print("Defender's turn")
        elif not unplaced:
            print("All units placed!")

    def _try_start_battle(self):
        """Try to start battle after placement."""
        result = self.battle.validate_placement_and_start()

        if not result["valid"]:
            print(f"Cannot start: {result['error']}")
            return

        from Battle import BattlePhaseUI

        self.phase = BattleGamePhase.PERSONAL_COMBAT_OFFER
        self.ui.set_phase(BattlePhaseUI.PERSONAL_COMBAT_OFFER)
        # Explicitly clear placement zones
        self.ui.valid_placement_hexes = []

        self.personal_combat_step = "defender_offer"
        self.personal_combat_defender_general = None
        self.personal_combat_attacker_general = None
        self.personal_combat_proposer = None

        print("\n" + "=" * 50)
        print("PERSONAL COMBAT PHASE")
        print("=" * 50)
        print("\nDefender is offered first chance to propose personal combat.")
        print("If accepted, each side chooses ONE general to duel.")
        print("Refusing when challenged: 8% troop loss!")
        print("\nDefender: Press Y to propose, N to decline")

    def _start_tactical_battle(self):
        """Start tactical battle."""
        from Battle import BattlePhaseUI

        self.phase = BattleGamePhase.BATTLE
        self.ui.set_phase(BattlePhaseUI.BATTLE)
        self.battle.phase = (
            self.battle.BattlePhase.TACTICAL
            if hasattr(self.battle, "BattlePhase")
            else None
        )
        print("\n" + "=" * 50)
        print("TACTICAL BATTLE")
        print("=" * 50)
        print("Controls:")
        print("  Click unit: Select")
        print("  Click hex: Move (if in range)")
        print("  Click enemy: Attack (if adjacent)")
        print("  F: Fire attack mode")
        print("  B: Bribe mode (commander only)")
        print("  ENTER: End turn")

    def _end_turn(self):
        """End current turn."""
        was_attacker = self.battle.turn == 0

        if not self.battle.next_turn():
            from Battle import BattlePhaseUI

            self.phase = BattleGamePhase.ENDED
            self.ui.set_phase(BattlePhaseUI.ENDED)
            return

        # New day
        if self.battle.turn == 0 and not was_attacker:
            print(f"\n>>> Day {self.battle.day}")

            old_weather = self.battle.weather
            self.battle.transition_weather()
            if self.battle.weather != old_weather:
                print(f"  Weather: {old_weather} -> {self.battle.weather}")

            fire_result = self.battle.process_daily_fire_effects()
            for _, msg in fire_result.get("extinguished", []):
                print(f"  {msg}")
            for _, msg in fire_result.get("new_fires", []):
                print(f"  {msg}")
            for dmg in fire_result.get("fire_damage", []):
                print(
                    f"  {dmg['unit'].get_officer_name()}: {dmg['casualties']} fire damage!"
                )

        self.ui.clear_selection()
        side = "Attacker" if self.battle.turn == 0 else "Defender"
        print(f"\n{side}'s turn (Day {self.battle.day})")

    def render(self):
        """Render the game."""
        self.ui.render()

        # Render reinforcement placement zones if in that phase
        if self.phase == BattleGamePhase.REINFORCEMENT_PLACEMENT:
            self._render_reinforcement_placement_zones()

        # Render attack direction indicators if in that phase
        if self.phase == BattleGamePhase.ATTACK_DIRECTION:
            self._render_attack_direction_indicators()

        # Render personal combat UI overlay
        if self.phase in [
            BattleGamePhase.PERSONAL_COMBAT_OFFER,
            BattleGamePhase.PERSONAL_COMBAT_SELECT,
        ]:
            self._render_personal_combat_overlay()
        elif self.phase == BattleGamePhase.BRIBE_SELECT:
            self._render_bribe_overlay()
        elif self.phase == BattleGamePhase.REINFORCEMENT_SELECT:
            if self.reinforcement_overlay:
                self.reinforcement_overlay.render()

    def _render_personal_combat_overlay(self):
        """Render personal combat UI overlay."""
        import pygame

        # Darken screen
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Dialog box (wider and taller for up to 10 units in 2 columns)
        box_width = 550
        box_height = 380
        x = (self.screen.get_width() - box_width) // 2
        y = (self.screen.get_height() - box_height) // 2

        s = pygame.Surface((box_width, box_height))
        s.set_alpha(240)
        s.fill((40, 20, 20))
        self.screen.blit(s, (x, y))
        pygame.draw.rect(self.screen, (200, 50, 50), (x, y, box_width, box_height), 3)

        font = pygame.font.SysFont(None, 28)
        small_font = pygame.font.SysFont(None, 20)

        # Title
        title = font.render("PERSONAL COMBAT", True, (255, 100, 100))
        self.screen.blit(title, (x + 20, y + 15))

        # Content based on step
        if self.personal_combat_step == "defender_offer":
            lines = [
                "The defender is offered first chance",
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

        elif self.personal_combat_step == "attacker_offer":
            lines = [
                "Defender declined.",
                "Attacker is offered chance to propose.",
            ]
            for i, line in enumerate(lines):
                text = small_font.render(line, True, (220, 220, 220))
                self.screen.blit(text, (x + 20, y + 50 + i * 18))

            text = font.render(
                "Attacker: Propose personal combat?", True, (255, 255, 255)
            )
            self.screen.blit(text, (x + 20, y + 100))
            text = small_font.render("[Y] Yes  [N] No", True, (200, 200, 200))
            self.screen.blit(text, (x + 40, y + 125))

        elif self.personal_combat_step == "defender_select":
            lines = ["Defender proposes! Select your champion (1-9, 0 for 10th):"]
            for i, line in enumerate(lines):
                text = small_font.render(line, True, (220, 220, 220))
                self.screen.blit(text, (x + 20, y + 50 + i * 18))

            # List available (up to 10, in two columns)
            available = [
                u
                for u in self.battle.defending_units
                if not u.is_defeated() and u.position
            ]
            # First column (1-5)
            for i, unit in enumerate(available[:5]):
                name = unit.get_officer_name()
                war = unit.get_war_ability()
                key_num = i + 1
                text = small_font.render(
                    f"[{key_num}] {name} (War {war})", True, (200, 200, 200)
                )
                self.screen.blit(text, (x + 40, y + 80 + i * 22))
            # Second column (6-10, key 0 for 10th)
            for i, unit in enumerate(available[5:10]):
                name = unit.get_officer_name()
                war = unit.get_war_ability()
                key_num = i + 6 if i < 4 else 0  # 6,7,8,9,0
                key_display = "0" if key_num == 0 else str(key_num)
                text = small_font.render(
                    f"[{key_display}] {name} (War {war})", True, (200, 200, 200)
                )
                self.screen.blit(text, (x + 260, y + 80 + i * 22))

            if self.personal_combat_defender_general:
                name = self.personal_combat_defender_general.get_officer_name()
                text = font.render(f"Selected: {name}", True, (100, 255, 100))
                self.screen.blit(text, (x + 20, y + 220))

        elif self.personal_combat_step == "attacker_select":
            lines = ["Attacker proposes! Select your champion (1-9, 0 for 10th):"]
            for i, line in enumerate(lines):
                text = small_font.render(line, True, (220, 220, 220))
                self.screen.blit(text, (x + 20, y + 50 + i * 18))

            available = [
                u
                for u in self.battle.attacking_units
                if not u.is_defeated() and u.position
            ]
            # First column (1-5)
            for i, unit in enumerate(available[:5]):
                name = unit.get_officer_name()
                war = unit.get_war_ability()
                key_num = i + 1
                text = small_font.render(
                    f"[{key_num}] {name} (War {war})", True, (200, 200, 200)
                )
                self.screen.blit(text, (x + 40, y + 80 + i * 22))
            # Second column (6-10, key 0 for 10th)
            for i, unit in enumerate(available[5:10]):
                name = unit.get_officer_name()
                war = unit.get_war_ability()
                key_num = i + 6 if i < 4 else 0  # 6,7,8,9,0
                key_display = "0" if key_num == 0 else str(key_num)
                text = small_font.render(
                    f"[{key_display}] {name} (War {war})", True, (200, 200, 200)
                )
                self.screen.blit(text, (x + 260, y + 80 + i * 22))

            if self.personal_combat_attacker_general:
                name = self.personal_combat_attacker_general.get_officer_name()
                text = font.render(f"Selected: {name}", True, (100, 255, 100))
                self.screen.blit(text, (x + 20, y + 220))

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

            text = font.render("Attacker: Accept challenge?", True, (255, 255, 255))
            self.screen.blit(text, (x + 20, y + 140))
            text = small_font.render("[Y] Accept  [N] Refuse", True, (200, 200, 200))
            self.screen.blit(text, (x + 40, y + 165))

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

            text = font.render("Defender: Accept challenge?", True, (255, 255, 255))
            self.screen.blit(text, (x + 20, y + 140))
            text = small_font.render("[Y] Accept  [N] Refuse", True, (200, 200, 200))
            self.screen.blit(text, (x + 40, y + 165))

    def _render_bribe_overlay(self):
        """Render bribe selection modal."""
        import pygame

        # Darken screen
        overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        self.screen.blit(overlay, (0, 0))

        # Dialog box
        box_width = 550
        box_height = 400 if self.bribe_step == "select_target" else 280
        x = (self.screen.get_width() - box_width) // 2
        y = (self.screen.get_height() - box_height) // 2

        s = pygame.Surface((box_width, box_height))
        s.set_alpha(240)
        s.fill((40, 30, 10))  # Gold-ish dark background
        self.screen.blit(s, (x, y))
        pygame.draw.rect(
            self.screen, (255, 215, 0), (x, y, box_width, box_height), 3
        )  # Gold border

        font = pygame.font.SysFont(None, 28)
        small_font = pygame.font.SysFont(None, 20)

        # Title
        title = font.render("BRIBE ATTEMPT", True, (255, 215, 0))
        self.screen.blit(title, (x + 20, y + 15))

        if self.bribe_step == "select_target":
            lines = ["Select enemy unit to bribe:"]
            for i, line in enumerate(lines):
                text = small_font.render(line, True, (220, 220, 200))
                self.screen.blit(text, (x + 20, y + 50 + i * 18))

            # Get enemy units
            if self.ui.selected_unit.is_attacker:
                enemies = [
                    u
                    for u in self.battle.defending_units
                    if not u.is_defeated() and u.position
                ]
            else:
                enemies = [
                    u
                    for u in self.battle.attacking_units
                    if not u.is_defeated() and u.position
                ]

            # First column (1-5)
            for i, unit in enumerate(enemies[:5]):
                name = unit.get_officer_name()
                war = unit.get_war_ability()
                loyalty = getattr(unit.officer, "Loyalty", 50)
                key_num = i + 1
                text = small_font.render(
                    f"[{key_num}] {name} (War {war}, Loy {loyalty})",
                    True,
                    (220, 220, 180),
                )
                self.screen.blit(text, (x + 40, y + 80 + i * 22))

            # Second column (6-10)
            for i, unit in enumerate(enemies[5:10]):
                name = unit.get_officer_name()
                war = unit.get_war_ability()
                loyalty = getattr(unit.officer, "Loyalty", 50)
                key_num = i + 6 if i < 4 else 0
                key_display = "0" if key_num == 0 else str(key_num)
                text = small_font.render(
                    f"[{key_display}] {name} (War {war}, Loy {loyalty})",
                    True,
                    (220, 220, 180),
                )
                self.screen.blit(text, (x + 280, y + 80 + i * 22))

            text = small_font.render("[ESC] Cancel", True, (200, 200, 200))
            self.screen.blit(text, (x + 20, y + box_height - 30))

        elif self.bribe_step == "enter_amount":
            lines = [
                f"Target: {self.bribe_target.get_officer_name()}",
                f"Loyalty: {getattr(self.bribe_target.officer, 'Loyalty', 50)}",
                "",
                "Enter bribe amount (1-99 gold):",
            ]
            for i, line in enumerate(lines):
                text = small_font.render(line, True, (220, 220, 200))
                self.screen.blit(text, (x + 20, y + 50 + i * 20))

            # Show entered amount
            amount_text = font.render(
                f"Amount: {self.bribe_amount} gold", True, (255, 255, 100)
            )
            self.screen.blit(amount_text, (x + 40, y + 140))

            # Instructions
            text = small_font.render(
                "Type digits (1-9, 0), BACKSPACE to delete", True, (180, 180, 180)
            )
            self.screen.blit(text, (x + 40, y + 175))

            text = small_font.render("[Y] Confirm  [N] Cancel", True, (200, 200, 200))
            self.screen.blit(text, (x + 40, y + 200))

    def _render_reinforcement_placement_zones(self):
        """Render reinforcement placement zones (blue highlights)."""
        import pygame

        # Draw valid placement zones
        for coord in self.reinforcement_valid_hexes:
            x, y_pos, width, height = self.ui.renderer.get_tile_rect(coord)
            s = pygame.Surface(
                (self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA
            )
            # Blue tint for reinforcements
            pygame.draw.rect(s, (0, 100, 255, 64), (x, y_pos, width, height))
            self.screen.blit(s, (0, 0))
            pygame.draw.rect(self.screen, (0, 150, 255), (x, y_pos, width, height), 2)

        # Draw instruction panel
        y = self.screen.get_height() - 100
        s = pygame.Surface((350, 90))
        s.set_alpha(200)
        s.fill((0, 0, 32))
        self.screen.blit(s, (10, y))

        font = pygame.font.SysFont(None, 24)
        small_font = pygame.font.SysFont(None, 20)

        text = font.render("REINFORCEMENT PLACEMENT", True, (100, 200, 255))
        self.screen.blit(text, (20, y + 5))

        if self.reinforcement_unit:
            name_text = small_font.render(
                f"Placing: {self.reinforcement_unit.get_officer_name()}",
                True,
                (255, 255, 255),
            )
            self.screen.blit(name_text, (20, y + 28))

        lines = [
            "Click blue zone to place",
            "SPACE: Auto-place",
            "ESC: Cancel",
        ]

        for i, line in enumerate(lines):
            text = small_font.render(line, True, (200, 200, 200))
            self.screen.blit(text, (20, y + 45 + i * 16))

    def _render_attack_direction_indicators(self):
        """Render attack direction indicators on adjacent hexes."""
        import pygame

        unit = self.ui.selected_unit
        if not unit or not unit.position:
            return

        # Get adjacent hexes
        adjacent_hexes = self.battle.grid.get_adjacent(unit.position)

        # Draw attack indicators on each adjacent hex
        for coord in adjacent_hexes:
            x, y_pos, width, height = self.ui.renderer.get_tile_rect(coord)

            # Red tint for attackable hexes
            s = pygame.Surface(
                (self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA
            )
            pygame.draw.rect(s, (255, 50, 50, 64), (x, y_pos, width, height))
            self.screen.blit(s, (0, 0))
            pygame.draw.rect(self.screen, (255, 100, 100), (x, y_pos, width, height), 2)

            # Draw sword icon in center
            cx = x + width // 2
            cy = y_pos + height // 2
            pygame.draw.line(
                self.screen, (255, 200, 200), (cx - 6, cy + 6), (cx + 6, cy - 6), 3
            )
            pygame.draw.line(
                self.screen, (255, 200, 200), (cx - 6, cy - 6), (cx + 6, cy + 6), 3
            )

        # Draw instruction panel
        y = self.screen.get_height() - 80
        s = pygame.Surface((350, 70))
        s.set_alpha(200)
        s.fill((32, 0, 0))
        self.screen.blit(s, (10, y))

        font = pygame.font.SysFont(None, 24)
        small_font = pygame.font.SysFont(None, 20)

        text = font.render("ATTACK DIRECTION MODE", True, (255, 150, 150))
        self.screen.blit(text, (20, y + 5))

        lines = [
            "Click red zone to attack",
            "Hidden units will be hit but stay hidden",
            "ESC: Cancel",
        ]

        for i, line in enumerate(lines):
            text = small_font.render(line, True, (200, 200, 200))
            self.screen.blit(text, (20, y + 25 + i * 16))

    def run(self):
        """Main game loop."""
        while self.running:
            self.handle_events()
            self.render()
            import pygame

            pygame.display.flip()
            pygame.time.Clock().tick(60)

        import pygame

        pygame.quit()
