"""
Battle unit representation.

A unit consists of an officer and their assigned soldiers.
"""

from typing import Optional, Any
from enum import Enum


class UnitState(Enum):
    """Possible states for a battle unit."""

    INACTIVE = 0  # Not yet placed on battlefield
    ACTIVE = 1  # On battlefield, can act
    ENGAGED = 2  # Adjacent to enemy, cannot move further
    MOVED = 3  # Has moved this turn
    ATTACKED = 4  # Has attacked this turn
    RETREATED = 5  # Retreating from battle
    CAPTURED = 6  # Captured by enemy
    DEFEATED = 7  # Defeated in battle
    IN_RESERVE = 8  # In reserve, not on map


class BattleUnit:
    """
    Represents a unit on the battlefield.

    A unit consists of:
    - Officer (general)
    - Soldiers assigned to them
    - Equipment and training
    - Current status
    """

    MAX_SOLDIERS_DISPLAY = 100  # Displayed as 0-100 (represents 0-10,000)
    MAX_MOBILITY = 6

    def __init__(self, officer: Any, soldiers: int = 0, is_attacker: bool = True):
        """
        Initialize battle unit.

        Args:
            officer: Officer object (from Officer.py)
            soldiers: Number of soldiers (0-100)
            is_attacker: True if attacking, False if defending
        """
        self.officer = officer
        self.soldiers = min(soldiers, self.MAX_SOLDIERS_DISPLAY)
        self.is_attacker = is_attacker

        # Unit stats
        self.training = getattr(officer, "TrainingLevel", 0)  # 0-100
        self.arms = getattr(officer, "Arms", 100)  # 0-100%
        self.loyalty = getattr(officer, "Loyalty", 50)  # 0-100

        # Battle state
        self.state = UnitState.INACTIVE
        self.position: Optional[Any] = None  # HexCoord
        self.mobility = self.calculate_mobility()
        self.max_mobility = self.mobility

        # Combat tracking
        self.has_moved = False
        self.has_attacked = False
        self.is_commander = False

        # Fire/burning
        self.is_burning = False
        self.turns_burning = 0

        # Bribe tracking
        self.bribe_attempts = 0
        self.times_bribed = 0

    def calculate_mobility(self) -> int:
        """
        Calculate base mobility from training.

        Returns:
            Mobility value (0-6)
        """
        # Max 6 mobility at 100 training
        if self.training >= 100:
            return self.MAX_MOBILITY
        return int(self.training / 16.67)  # 100/6 ≈ 16.67

    def get_effective_attack(self) -> float:
        """
        Calculate effective attack power.

        Returns:
            Attack value based on war, soldiers, and equipment
        """
        war = getattr(self.officer, "War", 50)

        # Base attack: war * soldiers / 100
        base_attack = (war * self.soldiers) / 100

        # Arms bonus
        arms_bonus = self.arms / 100  # 0.0 to 1.0

        # Training bonus
        training_bonus = self.training / 100  # 0.0 to 1.0

        return base_attack * (0.5 + arms_bonus * 0.25 + training_bonus * 0.25)

    def get_defense(self) -> float:
        """
        Calculate defense value.

        Returns:
            Defense value
        """
        war = getattr(self.officer, "War", 50)
        # Defense based on war ability and training
        return (war * 0.5 + self.training * 0.5) * (self.soldiers / 100)

    def take_damage(self, damage: float) -> int:
        """
        Apply damage to unit.

        Args:
            damage: Amount of damage to apply

        Returns:
            Soldiers lost
        """
        # Damage reduces soldiers
        soldiers_lost = int(damage)
        old_soldiers = self.soldiers
        self.soldiers = max(0, self.soldiers - soldiers_lost)

        actual_lost = old_soldiers - self.soldiers

        # Check for defeat
        if self.soldiers <= 0:
            self.state = UnitState.DEFEATED

        return actual_lost

    def is_defeated(self) -> bool:
        """
        Check if unit is defeated.

        Returns:
            True if defeated
        """
        return self.soldiers <= 0 or self.state == UnitState.DEFEATED

    def can_move(self) -> bool:
        """
        Check if unit can move this turn.

        Returns:
            True if can move
        """
        if self.state in [UnitState.DEFEATED, UnitState.CAPTURED, UnitState.RETREATED]:
            return False
        if self.has_moved:
            return False
        if self.mobility <= 0:
            return False
        return True

    def can_attack(self) -> bool:
        """
        Check if unit can attack this turn.

        Returns:
            True if can attack
        """
        if self.state in [UnitState.DEFEATED, UnitState.CAPTURED]:
            return False
        if self.has_attacked:
            return False
        if self.soldiers <= 0:
            return False
        return True

    def move_to(self, position: Any, mobility_cost: int):
        """
        Move unit to new position.

        Args:
            position: New HexCoord position
            mobility_cost: Cost of movement
        """
        self.position = position
        self.mobility -= mobility_cost
        self.has_moved = True

        if self.state == UnitState.INACTIVE:
            self.state = UnitState.ACTIVE

    def engage(self):
        """Mark unit as engaged (adjacent to enemy)."""
        self.state = UnitState.ENGAGED

    def end_turn(self):
        """End turn, reset flags."""
        self.has_moved = False
        self.has_attacked = False
        if self.state == UnitState.ENGAGED:
            self.state = UnitState.ACTIVE

        # Recover 1 mobility if rested (didn't move or attack)
        if not self.has_moved and not self.has_attacked:
            self.mobility = min(self.mobility + 1, self.max_mobility)

    def set_commander(self, is_commander: bool = True):
        """
        Set whether this unit is the commander.

        Args:
            is_commander: True if commander
        """
        self.is_commander = is_commander

    def get_officer_name(self) -> str:
        """
        Get officer name.

        Returns:
            Officer name string
        """
        if hasattr(self.officer, "GetName"):
            return self.officer.GetName()
        return getattr(self.officer, "name", "Unknown")

    def get_officer_id(self) -> int:
        """
        Get officer ID.

        Returns:
            Officer ID
        """
        return getattr(self.officer, "Id", 0)

    def get_war_ability(self) -> int:
        """
        Get officer war ability.

        Returns:
            War stat (0-100)
        """
        return getattr(self.officer, "War", 50)

    def get_intelligence(self) -> int:
        """
        Get officer intelligence.

        Returns:
            Intelligence stat (0-100)
        """
        return getattr(self.officer, "Int", 50)

    def get_charm(self) -> int:
        """
        Get officer charm.

        Returns:
            Charm stat (0-100)
        """
        return getattr(self.officer, "Chm", 50)

    def __repr__(self) -> str:
        """String representation."""
        return f"BattleUnit({self.get_officer_name()}, soldiers={self.soldiers})"

    def to_dict(self) -> dict:
        """
        Convert to dictionary for serialization.

        Returns:
            Dictionary representation
        """
        return {
            "officer_id": self.get_officer_id(),
            "officer_name": self.get_officer_name(),
            "soldiers": self.soldiers,
            "training": self.training,
            "arms": self.arms,
            "loyalty": self.loyalty,
            "mobility": self.mobility,
            "state": self.state.name,
            "is_attacker": self.is_attacker,
            "is_commander": self.is_commander,
            "position": str(self.position) if self.position else None,
        }


class ReservePool:
    """Manages reserve units not on the battlefield."""

    def __init__(self):
        """Initialize empty reserve pool."""
        self.units: list[BattleUnit] = []

    def add(self, unit: BattleUnit):
        """
        Add unit to reserve.

        Args:
            unit: Unit to add
        """
        unit.state = UnitState.IN_RESERVE
        self.units.append(unit)

    def remove(self, unit: BattleUnit) -> bool:
        """
        Remove unit from reserve.

        Args:
            unit: Unit to remove

        Returns:
            True if found and removed
        """
        if unit in self.units:
            self.units.remove(unit)
            return True
        return False

    def get_available(self) -> list[BattleUnit]:
        """
        Get all available reserve units.

        Returns:
            List of units in reserve
        """
        return [u for u in self.units if u.state == UnitState.IN_RESERVE]

    def __len__(self) -> int:
        """Number of units in reserve."""
        return len(self.units)

    def __repr__(self) -> str:
        """String representation."""
        return f"ReservePool({len(self)} units)"


if __name__ == "__main__":
    # Test BattleUnit
    print("Testing BattleUnit...")

    # Mock officer
    class MockOfficer:
        def __init__(self):
            self.Id = 1
            self.name = "Test Officer"
            self.War = 80
            self.Int = 70
            self.Chm = 60
            self.TrainingLevel = 80
            self.Arms = 100
            self.Loyalty = 90

        def GetName(self):
            return self.name

    officer = MockOfficer()
    unit = BattleUnit(officer, soldiers=50, is_attacker=True)

    print(f"Created: {unit}")
    print(f"Mobility: {unit.mobility}")
    print(f"Attack: {unit.get_effective_attack():.1f}")
    print(f"Can move: {unit.can_move()}")
    print(f"State: {unit.state.name}")

    # Test damage
    lost = unit.take_damage(10)
    print(f"Took 10 damage, lost {lost} soldiers, remaining: {unit.soldiers}")

    # Test reserve pool
    reserve = ReservePool()
    reserve.add(unit)
    print(f"Added to reserve: {reserve}")
    print(f"Available: {len(reserve.get_available())}")

    print("BattleUnit test complete!")
