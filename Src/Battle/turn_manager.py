"""
Turn manager for battle flow.

Handles turn phases, action processing, and state transitions.
"""

from typing import Optional, List, Any
from enum import Enum, auto

from .battle_unit import BattleUnit, UnitState
from .hex_grid import HexCoord


class TurnPhase(Enum):
    """Phases within a single turn."""

    SELECT_UNIT = auto()  # Select which unit to act
    SELECT_ACTION = auto()  # Select action type
    SELECT_TARGET = auto()  # Select target for action
    EXECUTE = auto()  # Execute the action
    END = auto()  # End turn


class TurnManager:
    """
    Manages turn flow for battle.

    Handles:
    - Unit selection
    - Action selection
    - Target selection
    - Action execution
    """

    def __init__(self, battle_engine: Any):
        """
        Initialize turn manager.

        Args:
            battle_engine: Reference to BattleEngine
        """
        self.engine = battle_engine
        self.phase = TurnPhase.SELECT_UNIT
        self.selected_unit: Optional[BattleUnit] = None
        self.selected_action: Optional[str] = None
        self.selected_target: Optional[Any] = None

        # Available actions
        self.actions: List[str] = []
        self.valid_targets: List[Any] = []

    def start_turn(self):
        """Start a new turn."""
        self.phase = TurnPhase.SELECT_UNIT
        self.selected_unit = None
        self.selected_action = None
        self.selected_target = None
        self.actions = []
        self.valid_targets = []

    def get_available_units(self) -> List[BattleUnit]:
        """
        Get units that can act this turn.

        Returns:
            List of available units
        """
        units = self.engine.get_current_side_units()
        return [u for u in units if u.can_move() or u.can_attack()]

    def select_unit(self, unit: BattleUnit) -> bool:
        """
        Select a unit to act.

        Args:
            unit: Unit to select

        Returns:
            True if successful
        """
        if unit not in self.get_available_units():
            return False

        self.selected_unit = unit
        self.phase = TurnPhase.SELECT_ACTION
        return True

    def get_available_actions(self) -> List[str]:
        """
        Get available actions for selected unit.

        Returns:
            List of action names
        """
        if not self.selected_unit:
            return []

        actions = []

        if self.selected_unit.can_move():
            actions.append("move")

        if self.selected_unit.can_attack():
            actions.extend(["attack", "fire", "charge"])

        # Tactics
        actions.extend(["bribe", "view"])

        # Always available
        actions.extend(["standby", "flee"])

        return actions

    def select_action(self, action: str) -> bool:
        """
        Select an action.

        Args:
            action: Action name

        Returns:
            True if valid action
        """
        if action not in self.get_available_actions():
            return False

        self.selected_action = action
        self.phase = TurnPhase.SELECT_TARGET
        return True

    def get_valid_targets(self) -> List[Any]:
        """
        Get valid targets for selected action.

        Returns:
            List of valid targets
        """
        if not self.selected_unit or not self.selected_action:
            return []

        targets = []

        if self.selected_action == "move":
            # Get reachable hexes
            targets = self.engine.grid.get_movement_range(
                self.selected_unit.position, self.selected_unit.mobility
            )

        elif self.selected_action in ["attack", "charge", "fire"]:
            # Get adjacent enemy units
            adjacent = self.engine.grid.get_adjacent(self.selected_unit.position)
            for coord in adjacent:
                hex_obj = self.engine.grid.get_hex(coord)
                if hex_obj and hex_obj.unit:
                    # Check if enemy
                    if hex_obj.unit.is_attacker != self.selected_unit.is_attacker:
                        targets.append(hex_obj.unit)

        elif self.selected_action == "bribe":
            # Get adjacent enemy units
            adjacent = self.engine.grid.get_adjacent(self.selected_unit.position)
            for coord in adjacent:
                hex_obj = self.engine.grid.get_hex(coord)
                if hex_obj and hex_obj.unit:
                    if hex_obj.unit.is_attacker != self.selected_unit.is_attacker:
                        targets.append(hex_obj.unit)

        elif self.selected_action == "view":
            # Can view any enemy unit
            enemy_units = (
                self.engine.get_attacking_units_on_map()
                if not self.selected_unit.is_attacker
                else self.engine.get_defending_units_on_map()
            )
            targets = enemy_units

        self.valid_targets = targets
        return targets

    def select_target(self, target: Any) -> bool:
        """
        Select a target.

        Args:
            target: Target (HexCoord or BattleUnit)

        Returns:
            True if valid target
        """
        if target not in self.valid_targets:
            return False

        self.selected_target = target
        self.phase = TurnPhase.EXECUTE
        return True

    def execute_action(self) -> bool:
        """
        Execute the selected action.

        Returns:
            True if successful
        """
        if not self.selected_unit or not self.selected_action:
            return False

        success = False

        try:
            if self.selected_action == "move":
                success = self._execute_move()
            elif self.selected_action == "attack":
                success = self._execute_attack()
            elif self.selected_action == "charge":
                success = self._execute_charge()
            elif self.selected_action == "fire":
                success = self._execute_fire()
            elif self.selected_action == "bribe":
                success = self._execute_bribe()
            elif self.selected_action == "view":
                success = self._execute_view()
            elif self.selected_action == "standby":
                success = self._execute_standby()
            elif self.selected_action == "flee":
                success = self._execute_flee()

            if success:
                self.engine.log_action(
                    f"{self.selected_unit.get_officer_name()} used {self.selected_action}"
                )

        except Exception as e:
            print(f"Error executing action: {e}")
            success = False

        self.phase = TurnPhase.END
        return success

    def _execute_move(self) -> bool:
        """Execute move action."""
        if not isinstance(self.selected_target, HexCoord):
            return False

        target_hex = self.engine.grid.get_hex(self.selected_target)
        if not target_hex:
            return False

        # Calculate mobility cost
        cost = target_hex.get_movement_cost()

        # Move unit
        old_pos = self.selected_unit.position
        if self.engine.grid.place_unit(self.selected_unit, self.selected_target):
            self.selected_unit.move_to(self.selected_target, cost)

            # Check if adjacent to enemy (ends turn)
            enemy_units = (
                self.engine.get_defending_units_on_map()
                if self.selected_unit.is_attacker
                else self.engine.get_attacking_units_on_map()
            )

            if self.engine.grid.is_adjacent_to_enemy(self.selected_target, enemy_units):
                self.selected_unit.engage()

            return True

        return False

    def _execute_attack(self) -> bool:
        """Execute normal attack."""
        if not isinstance(self.selected_target, BattleUnit):
            return False

        # Combat calculation (simplified)
        attacker = self.selected_unit
        defender = self.selected_target

        damage_to_defender = attacker.get_effective_attack() * 1.0
        damage_to_attacker = defender.get_effective_attack() * 0.6

        defender.take_damage(damage_to_defender)
        attacker.take_damage(damage_to_attacker)

        attacker.has_attacked = True

        return True

    def _execute_charge(self) -> bool:
        """Execute charge attack."""
        if not isinstance(self.selected_target, BattleUnit):
            return False

        attacker = self.selected_unit
        defender = self.selected_target

        # Heavy casualties on both sides
        damage_to_defender = attacker.get_effective_attack() * 1.5
        damage_to_attacker = defender.get_effective_attack() * 1.2

        defender.take_damage(damage_to_defender)
        attacker.take_damage(damage_to_attacker)

        attacker.has_attacked = True

        return True

    def _execute_fire(self) -> bool:
        """Execute fire attack."""
        # Fire attack sets hex on fire, not unit
        # Simplified for now
        self.engine.log.append(
            f"{self.selected_unit.get_officer_name()} attempts fire attack"
        )
        attacker.has_attacked = True
        return True

    def _execute_bribe(self) -> bool:
        """Execute bribe attempt."""
        if not isinstance(self.selected_target, BattleUnit):
            return False

        # Simplified bribe logic
        target = self.selected_target

        # Check if bribable
        if target.loyalty > 90:
            # Very hard to bribe
            return False

        # Success chance based on loyalty
        import random

        success_chance = max(0.05, (100 - target.loyalty) / 100)

        if random.random() < success_chance:
            # Switch sides
            target.is_attacker = not target.is_attacker
            return True

        return False

    def _execute_view(self) -> bool:
        """Execute view action (costs 10 gold)."""
        # Just log for now
        if isinstance(self.selected_target, BattleUnit):
            unit = self.selected_target
            self.engine.log.append(
                f"View: {unit.get_officer_name()} - "
                f"War:{unit.get_war_ability()} Int:{unit.get_intelligence()} "
                f"Loyalty:{unit.loyalty} Soldiers:{unit.soldiers}"
            )
            return True
        return False

    def _execute_standby(self) -> bool:
        """Execute standby action."""
        self.selected_unit.has_moved = True
        self.selected_unit.has_attacked = True
        return True

    def _execute_flee(self) -> bool:
        """Execute flee/retreat action."""
        self.selected_unit.state = UnitState.RETREATED
        self.engine.grid.remove_unit(self.selected_unit.position)
        return True

    def end_turn(self):
        """End current turn."""
        self.phase = TurnPhase.SELECT_UNIT
        self.selected_unit = None
        self.selected_action = None
        self.selected_target = None
        self.actions = []
        self.valid_targets = []


if __name__ == "__main__":
    # Test turn manager
    print("Testing TurnManager...")

    # Mock battle engine
    class MockEngine:
        def __init__(self):
            self.grid = None
            self.log = []

        def get_current_side_units(self):
            return []

        def get_attacking_units_on_map(self):
            return []

        def get_defending_units_on_map(self):
            return []

        def log_action(self, msg):
            self.log.append(msg)

    engine = MockEngine()
    manager = TurnManager(engine)

    print(f"Created: {manager}")
    print(f"Phase: {manager.phase.name}")

    print("TurnManager test complete!")
