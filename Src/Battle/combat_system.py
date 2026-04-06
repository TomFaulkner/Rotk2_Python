"""
Combat system for ROTK2 battles.

Handles attack calculations, damage, and combat resolution.
"""

import random
from typing import List, Tuple, Optional
from enum import Enum


class AttackType(Enum):
    """Types of attacks available."""

    NORMAL = "normal"  # Single unit attack
    SIMULTANEOUS = "simultaneous"  # Multiple units attack together
    CHARGE = "charge"  # Heavy damage to both sides
    FIRE = "fire"  # Set hex on fire


class CombatResult:
    """Result of a combat exchange."""

    def __init__(self):
        self.attacker_damage_dealt = 0
        self.attacker_damage_taken = 0
        self.defender_damage_dealt = 0
        self.defender_damage_taken = 0
        self.attacker_casualties = 0
        self.defender_casualties = 0
        self.defender_defeated = False
        self.attacker_defeated = False
        self.capture_attempt = False
        self.messages: List[str] = []

    def add_message(self, msg: str):
        """Add a message to the result."""
        self.messages.append(msg)

    def __repr__(self):
        return (
            f"CombatResult(A:{self.attacker_casualties}/D:{self.defender_casualties})"
        )


class CombatSystem:
    """
    Handles all combat calculations.
    """

    @staticmethod
    def calculate_normal_attack(attacker, defender) -> CombatResult:
        """
        Calculate normal attack.

        Single unit vs single unit.
        Moderate casualties on both sides.
        """
        result = CombatResult()

        # Get attack values
        att_attack = attacker.get_effective_attack()
        def_attack = defender.get_effective_attack()

        # Defense modifiers
        def_defense = defender.get_defense()

        # Calculate damage
        # Normal attack: attacker deals 100%, takes 60%
        damage_to_defender = max(1, att_attack * 1.0 - def_defense * 0.2)
        damage_to_attacker = max(1, def_attack * 0.6 - attacker.get_defense() * 0.2)

        # Apply some randomness (±20%)
        damage_to_defender = int(damage_to_defender * random.uniform(0.8, 1.2))
        damage_to_attacker = int(damage_to_attacker * random.uniform(0.8, 1.2))

        result.attacker_damage_dealt = damage_to_defender
        result.defender_damage_taken = damage_to_defender
        result.defender_damage_dealt = damage_to_attacker
        result.attacker_damage_taken = damage_to_attacker

        # Apply damage
        result.defender_casualties = defender.take_damage(damage_to_defender)
        result.attacker_casualties = attacker.take_damage(damage_to_attacker)

        # Check defeats
        result.defender_defeated = defender.is_defeated()
        result.attacker_defeated = attacker.is_defeated()

        # Messages
        result.add_message(
            f"{attacker.get_officer_name()} attacks {defender.get_officer_name()}"
        )
        result.add_message(
            f"Dealt {result.defender_casualties} damage, took {result.attacker_casualties}"
        )

        if result.defender_defeated:
            result.add_message(f"{defender.get_officer_name()} defeated!")
            result.capture_attempt = True

        return result

    @staticmethod
    def calculate_simultaneous_attack(attackers: List, defender) -> CombatResult:
        """
        Calculate simultaneous attack.

        Multiple attackers vs single defender.
        Low casualties for attackers, high for defender.
        """
        result = CombatResult()

        # Combined attack power
        combined_attack = sum(a.get_effective_attack() for a in attackers)
        def_attack = defender.get_effective_attack()
        def_defense = defender.get_defense()

        # Simultaneous: combined 120% damage, each attacker takes 30%
        damage_to_defender = max(1, combined_attack * 1.2 - def_defense * 0.3)
        damage_per_attacker = max(1, def_attack * 0.3)

        # Randomness
        damage_to_defender = int(damage_to_defender * random.uniform(0.9, 1.1))
        damage_per_attacker = int(damage_per_attacker * random.uniform(0.8, 1.2))

        result.defender_damage_taken = damage_to_defender
        result.defender_casualties = defender.take_damage(damage_to_defender)

        # Damage to each attacker
        for attacker in attackers:
            casualties = attacker.take_damage(damage_per_attacker)
            result.attacker_casualties += casualties
            if attacker.is_defeated():
                result.attacker_defeated = True

        result.defender_defeated = defender.is_defeated()

        # Messages
        attacker_names = ", ".join(a.get_officer_name() for a in attackers)
        result.add_message(f"Simultaneous attack on {defender.get_officer_name()}")
        result.add_message(f"By: {attacker_names}")
        result.add_message(f"Defender took {result.defender_casualties} damage")

        if result.defender_defeated:
            result.add_message(f"{defender.get_officer_name()} defeated!")
            result.capture_attempt = True

        return result

    @staticmethod
    def calculate_charge_attack(attacker, defender) -> CombatResult:
        """
        Calculate charge attack.

        Heavy casualties on both sides.
        Good for overwhelming weak units.
        """
        result = CombatResult()

        att_attack = attacker.get_effective_attack()
        def_attack = defender.get_effective_attack()

        # Charge: 150% damage to defender, 120% to attacker
        damage_to_defender = int(att_attack * 1.5 * random.uniform(0.9, 1.3))
        damage_to_attacker = int(def_attack * 1.2 * random.uniform(0.9, 1.3))

        result.attacker_damage_dealt = damage_to_defender
        result.defender_damage_taken = damage_to_defender
        result.defender_damage_dealt = damage_to_attacker
        result.attacker_damage_taken = damage_to_attacker

        # Apply damage
        result.defender_casualties = defender.take_damage(damage_to_defender)
        result.attacker_casualties = attacker.take_damage(damage_to_attacker)

        result.defender_defeated = defender.is_defeated()
        result.attacker_defeated = attacker.is_defeated()

        # Messages
        result.add_message(
            f"{attacker.get_officer_name()} CHARGES {defender.get_officer_name()}!"
        )
        result.add_message(
            f"Heavy casualties: A:{result.attacker_casualties} D:{result.defender_casualties}"
        )

        if result.defender_defeated:
            result.add_message(f"{defender.get_officer_name()} overwhelmed!")
            result.capture_attempt = True

        if result.attacker_defeated:
            result.add_message(f"{attacker.get_officer_name()} also fell!")

        return result

    @staticmethod
    def can_attack(attacker, defender, grid) -> bool:
        """
        Check if attacker can attack defender.

        Args:
            attacker: Attacking unit
            defender: Defending unit
            grid: HexGrid

        Returns:
            True if attack is possible
        """
        # Must be adjacent
        if not attacker.position or not defender.position:
            return False

        adjacent = grid.get_adjacent(attacker.position)
        if defender.position not in adjacent:
            return False

        # Must be enemies
        if attacker.is_attacker == defender.is_attacker:
            return False

        # Both must be active
        if attacker.is_defeated() or defender.is_defeated():
            return False

        return True

    @staticmethod
    def get_adjacent_enemies(unit, grid, all_units: List) -> List:
        """
        Get all enemy units adjacent to this unit.

        Args:
            unit: The unit
            grid: HexGrid
            all_units: All units in battle

        Returns:
            List of adjacent enemy units
        """
        if not unit.position:
            return []

        adjacent = grid.get_adjacent(unit.position)
        enemies = []

        for enemy in all_units:
            if enemy.is_attacker != unit.is_attacker and not enemy.is_defeated():
                if enemy.position in adjacent:
                    enemies.append(enemy)

        return enemies

    @staticmethod
    def get_adjacent_allies(unit, grid, all_units: List) -> List:
        """
        Get all friendly units adjacent to this unit.

        Args:
            unit: The unit
            grid: HexGrid
            all_units: All units in battle

        Returns:
            List of adjacent friendly units
        """
        if not unit.position:
            return []

        adjacent = grid.get_adjacent(unit.position)
        allies = []

        for ally in all_units:
            if (
                ally.is_attacker == unit.is_attacker
                and ally != unit
                and not ally.is_defeated()
            ):
                if ally.position in adjacent:
                    allies.append(ally)

        return allies


if __name__ == "__main__":
    # Test combat system
    print("Testing CombatSystem...")

    # Mock units
    class MockUnit:
        def __init__(self, name, war, soldiers, is_attacker):
            self.name = name
            self._war = war
            self.soldiers = soldiers
            self.is_attacker = is_attacker
            self.position = None

        def get_officer_name(self):
            return self.name

        def get_effective_attack(self):
            return (self._war * self.soldiers) / 100

        def get_defense(self):
            return (self._war * self.soldiers) / 200

        def take_damage(self, dmg):
            lost = min(self.soldiers, int(dmg / 10))
            self.soldiers -= lost
            return lost

        def is_defeated(self):
            return self.soldiers <= 0

    # Test normal attack
    print("\n1. Normal Attack:")
    attacker = MockUnit("Attacker", 80, 100, True)
    defender = MockUnit("Defender", 70, 80, False)

    result = CombatSystem.calculate_normal_attack(attacker, defender)
    print(f"   Attacker dealt: {result.defender_casualties}")
    print(f"   Attacker took: {result.attacker_casualties}")
    print(f"   Defender remaining: {defender.soldiers}")
    for msg in result.messages:
        print(f"   > {msg}")

    # Test charge attack
    print("\n2. Charge Attack:")
    attacker2 = MockUnit("Attacker", 90, 100, True)
    defender2 = MockUnit("Defender", 60, 50, False)

    result = CombatSystem.calculate_charge_attack(attacker2, defender2)
    print(f"   Attacker dealt: {result.defender_casualties}")
    print(f"   Attacker took: {result.attacker_casualties}")
    print(f"   Defender defeated: {result.defender_defeated}")
    for msg in result.messages:
        print(f"   > {msg}")

    # Test simultaneous attack
    print("\n3. Simultaneous Attack:")
    atk1 = MockUnit("Ally 1", 70, 80, True)
    atk2 = MockUnit("Ally 2", 75, 80, True)
    defender3 = MockUnit("Defender", 85, 100, False)

    result = CombatSystem.calculate_simultaneous_attack([atk1, atk2], defender3)
    print(f"   Total casualties to defender: {result.defender_casualties}")
    print(f"   Total casualties to attackers: {result.attacker_casualties}")
    for msg in result.messages:
        print(f"   > {msg}")

    print("\nCombatSystem test complete!")
