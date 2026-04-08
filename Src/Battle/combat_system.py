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
        self.pass_through_hex = None  # For charge attacks that pass through
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

    # Terrain defense multipliers - how much damage is REDUCED
    # 1.0 = no reduction, 0.5 = 50% damage reduction
    TERRAIN_DEFENSE_MULTIPLIER = {
        "water": 1.00,  # 0% blocked - no reduction
        "plains": 0.80,  # 20% blocked
        "grass": 0.80,  # 20% blocked
        "forest": 0.80,  # 20% blocked
        "hills": 0.70,  # ~30% blocked
        "fort": 0.60,  # 40% blocked
        "castle": 0.50,  # 50% blocked
        "mountain": 0.65,  # 35% blocked
    }

    @staticmethod
    def get_terrain_defense_multiplier(terrain_name: str) -> float:
        """
        Get damage reduction multiplier based on defender's terrain.

        Args:
            terrain_name: Name of the terrain

        Returns:
            Multiplier (1.0 = no reduction, 0.5 = 50% reduction)
        """
        return CombatSystem.TERRAIN_DEFENSE_MULTIPLIER.get(terrain_name.lower(), 1.0)

    @staticmethod
    def calculate_normal_attack(attacker, defender, grid=None) -> CombatResult:
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

        # Apply terrain defense multiplier to damage TO defender
        # Defender's terrain reduces damage they receive
        if grid and defender.position:
            defender_hex = grid.get_hex(defender.position)
            if defender_hex:
                terrain_mult = CombatSystem.get_terrain_defense_multiplier(
                    defender_hex.terrain.name
                )
                damage_to_defender *= terrain_mult

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
    def calculate_simultaneous_attack(
        attackers: List, defender, grid=None
    ) -> CombatResult:
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

        # Apply terrain defense multiplier to damage TO defender
        if grid and defender.position:
            defender_hex = grid.get_hex(defender.position)
            if defender_hex:
                terrain_mult = CombatSystem.get_terrain_defense_multiplier(
                    defender_hex.terrain.name
                )
                damage_to_defender *= terrain_mult

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
    def calculate_charge_attack(attacker, defender, grid=None) -> CombatResult:
        """
        Calculate charge attack.

        Heavy casualties on both sides.
        Good for overwhelming weak units.
        May pass through to hex behind defender based on strength difference.
        """
        result = CombatResult()

        # Heavy mutual damage (boosted from normal)
        att_attack = attacker.get_effective_attack()
        def_attack = defender.get_effective_attack()

        # Charge: 160% damage to defender, 140% to attacker
        damage_to_defender = att_attack * 1.6 * random.uniform(0.9, 1.3)
        damage_to_attacker = def_attack * 1.4 * random.uniform(0.9, 1.3)

        # Apply terrain defense multiplier to damage TO defender
        if grid and defender.position:
            defender_hex = grid.get_hex(defender.position)
            if defender_hex:
                terrain_mult = CombatSystem.get_terrain_defense_multiplier(
                    defender_hex.terrain.name
                )
                damage_to_defender *= terrain_mult

        damage_to_defender = int(damage_to_defender)
        damage_to_attacker = int(damage_to_attacker)

        result.attacker_damage_dealt = damage_to_defender
        result.defender_damage_taken = damage_to_defender
        result.defender_damage_dealt = damage_to_attacker
        result.attacker_damage_taken = damage_to_attacker

        # Apply damage
        result.defender_casualties = defender.take_damage(damage_to_defender)
        result.attacker_casualties = attacker.take_damage(damage_to_attacker)

        result.defender_defeated = defender.is_defeated()
        result.attacker_defeated = attacker.is_defeated()

        # Calculate pass-through chance based on strength difference
        # strength = war*3 + skill + arms + troops/1000
        if (
            not result.attacker_defeated
            and grid
            and attacker.position
            and defender.position
        ):
            # Get unit stats for strength calculation
            att_war = attacker.get_war_ability()
            def_war = defender.get_war_ability()
            att_skill = getattr(attacker.officer, "Skill", 50)
            def_skill = getattr(defender.officer, "Skill", 50)
            att_arms = attacker.arms
            def_arms = defender.arms
            att_troops = attacker.soldiers  # In game this would be actual troop count
            def_troops = defender.soldiers

            # Calculate strength
            att_strength = att_war * 3 + att_skill + att_arms + att_troops // 10
            def_strength = def_war * 3 + def_skill + def_arms + def_troops // 10
            strength_diff = att_strength - def_strength

            # Pass-through chance: (strength_diff / 150) + 0.5, clamped 10%-95%
            pass_through_chance = min(0.95, max(0.10, (strength_diff / 150) + 0.5))

            # Calculate hex behind defender
            from .hex_grid import HexCoord

            dx = defender.position.col - attacker.position.col
            dy = defender.position.row - attacker.position.row

            behind_col = defender.position.col + dx
            behind_row = defender.position.row + dy
            behind_hex = HexCoord(behind_row, behind_col)

            # Check if we can pass through
            behind_hex_obj = grid.get_hex(behind_hex)
            can_pass_through = (
                behind_hex_obj
                and not behind_hex_obj.unit  # No unit there
                and not behind_hex_obj.is_burning  # Not on fire
                and
                # Water doesn't block pass-through (though it's a bad strategy)
                random.random() < pass_through_chance
            )

            if can_pass_through:
                result.pass_through_hex = behind_hex
                result.add_message(f"Charge breaks through! Moved to {behind_hex}")
            else:
                result.add_message("Charge stopped cold!")

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
    def can_start_fire(unit, target_hex, grid, weather: str = "clear") -> bool:
        """
        Check if unit can start a fire on a hex.

        Args:
            unit: The unit attempting to start fire
            target_hex: HexCoord to target
            grid: HexGrid
            weather: Current weather condition

        Returns:
            True if fire can be started
        """
        if not unit.position:
            return False

        # Must be adjacent to target hex
        adjacent = grid.get_adjacent(unit.position)
        if target_hex not in adjacent:
            return False

        # Check if hex exists and isn't already burning
        hex_obj = grid.get_hex(target_hex)
        if not hex_obj:
            return False
        if hex_obj.is_burning:
            return False

        # Can't start fire on water or in storm
        from .terrain import TerrainType

        if hex_obj.terrain == TerrainType.WATER:
            return False
        if weather == "storm":
            return False

        return True

    @staticmethod
    def calculate_fire_success(
        unit, target_hex, grid, weather: str = "clear", wind_direction: str = None
    ) -> tuple:
        """
        Calculate fire attack success.

        Formula based on ROTK2 mechanics:
        - Base chance = (intelligence^2) / 12000
        - 100 Intelligence = guaranteed success (when possible)
        - Terrain resistance affects difficulty
        - Weather affects flammability

        Args:
            unit: The unit attempting to start fire
            target_hex: HexCoord to target
            grid: HexGrid
            weather: Current weather (sunny, clear, cloudy, rain, storm)
            wind_direction: Wind direction for spread calculation

        Returns:
            Tuple of (success: bool, message: str, spread_hexes: List[HexCoord])
        """
        intelligence = unit.get_intelligence()
        hex_obj = grid.get_hex(target_hex)
        terrain_name = hex_obj.terrain.name.lower() if hex_obj else "plains"

        # Max-stat magic: 100 Intel = guaranteed when possible
        if intelligence == 100:
            hex_obj.set_burning(True)
            return (True, f"Fire started on {target_hex}! (Master strategist)", [])

        # Base chance = (intel^2) / 12000
        # 100 intel = 83.3%, 80 intel = 53.3%, 50 intel = 20.8%
        base_chance = (intelligence**2) / 12000

        # Terrain resistance
        terrain_resistance = {
            "plains": 1.0,
            "grass": 1.0,
            "hills": 1.0,
            "mountains": 0.85,
            "forest": 1.6,  # Forests burn MORE easily
            "castle": 0.25,  # Castles are hard to burn
            "fort": 0.35,
        }.get(terrain_name, 1.0)

        # Weather modifier (ROTK2 accurate)
        weather_mod = {
            "sunny": 1.4,
            "light_clouds": 1.2,
            "dark_clouds": 0.7,
            "storm": 0.0,  # Can't start in storm
        }.get(weather, 1.0)

        final_chance = base_chance * terrain_resistance * weather_mod
        final_chance = min(final_chance, 0.95)  # Cap at 95%

        # Roll for success
        if random.random() >= final_chance:
            return (False, "Fire failed to catch!", [])

        # Success! Mark hex as burning
        hex_obj.set_burning(True)

        # Fire spreads at the start of each day (next turn), not immediately
        # For now, just report success
        message = f"Fire started on {target_hex}!"
        if terrain_name in ["castle", "fort"]:
            message += " (Difficult terrain!)"

        return (True, message, [])

    @staticmethod
    def process_fires(
        grid, wind_direction: str = None, weather: str = "clear"
    ) -> tuple:
        """
        Process all fires: spread to adjacent hexes and try to extinguish.
        Called at the start of each day (every 2 turns).

        Args:
            grid: HexGrid
            wind_direction: Direction wind is blowing
            weather: Current weather (rain immediately extinguishes all fires)

        Returns:
            Tuple of (new_fires: List[tuple], extinguished: List[HexCoord])
        """
        from .hex_grid import HexCoord

        # Storm (rain) immediately extinguishes ALL fires
        if weather == "storm":
            extinguished = []
            for coord, hex_obj in grid.hexes.items():
                if hex_obj.is_burning:
                    hex_obj.extinguish()
                    extinguished.append(coord)
            if extinguished:
                return (
                    [],
                    [
                        (coord, f"Storm extinguished fire at {coord}!")
                        for coord in extinguished
                    ],
                )
            return ([], [])

        new_fires = []
        extinguished = []
        burning_hexes = [
            coord for coord, hex_obj in grid.hexes.items() if hex_obj.is_burning
        ]

        # First, try to extinguish existing fires naturally
        for burning_coord in burning_hexes:
            hex_obj = grid.get_hex(burning_coord)
            if hex_obj.try_extinguish():
                extinguished.append(
                    (burning_coord, f"Fire at {burning_coord} died out naturally")
                )

        # Get updated list of still-burning hexes
        burning_hexes = [
            coord for coord, hex_obj in grid.hexes.items() if hex_obj.is_burning
        ]

        # Then spread remaining fires
        for burning_coord in burning_hexes:
            adjacent = grid.get_adjacent(burning_coord)
            for adj_coord in adjacent:
                adj_hex = grid.get_hex(adj_coord)
                if not adj_hex or adj_hex.is_burning:
                    continue

                # Base spread chance
                spread_chance = 0.35  # 35% base

                # Terrain affects spread
                terrain_name = adj_hex.terrain.name.lower()
                if terrain_name == "forest":
                    spread_chance += 0.25  # Forests spread fire easily
                elif terrain_name in ["plains", "grass"]:
                    spread_chance += 0.10
                elif terrain_name == "hills":
                    spread_chance += 0.05
                elif terrain_name in ["castle", "fort"]:
                    spread_chance -= 0.25  # Hard to burn structures
                elif terrain_name == "water":
                    continue  # Can't burn water

                # Wind direction increases spread
                if wind_direction:
                    # Check if this hex is in wind direction from burning hex
                    # Simplified: just add bonus for now
                    spread_chance += 0.15

                # Cap spread chance
                spread_chance = min(0.80, max(0.05, spread_chance))

                if random.random() < spread_chance:
                    adj_hex.set_burning(True)
                    new_fires.append((adj_coord, f"Fire spread to {adj_coord}!"))

        return (new_fires, extinguished)

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

    @staticmethod
    def get_allies_adjacent_to_target(attacker, target, grid, all_units: List) -> List:
        """
        Get all friendly units adjacent to the target (for simultaneous attacks).

        Args:
            attacker: The attacking unit
            target: The target unit being attacked
            grid: HexGrid
            all_units: All units in battle

        Returns:
            List of allies adjacent to the target who can help attack
        """
        if not target.position:
            return []

        target_adjacent = grid.get_adjacent(target.position)
        helping_allies = []

        for unit in all_units:
            if (
                unit.is_attacker == attacker.is_attacker
                and unit != attacker
                and not unit.is_defeated()
                and unit.can_attack()
            ):
                if unit.position in target_adjacent:
                    helping_allies.append(unit)

        return helping_allies

    @staticmethod
    def can_challenge_to_duel(challenger, target, day: int) -> bool:
        """
        Check if challenger can challenge target to a duel.

        Args:
            challenger: Unit issuing the challenge
            target: Unit being challenged
            day: Current battle day (duels only on Day 1)

        Returns:
            True if duel can be issued
        """
        # Duels only on Day 1
        if day != 1:
            return False

        # Must be enemies
        if challenger.is_attacker == target.is_attacker:
            return False

        # Both must be commanders
        if not challenger.is_commander or not target.is_commander:
            return False

        # Both must be alive and on the battlefield
        if challenger.is_defeated() or target.is_defeated():
            return False

        # Must be adjacent
        if not challenger.position or not target.position:
            return False

        return True

    @staticmethod
    def resolve_duel(attacker, defender, max_rounds: int = 10) -> dict:
        """
        Resolve a personal combat duel between two officers.

        Formula based on ROTK2 mechanics:
        - Each officer has STAMINA equal to their War stat (separate from damage calc)
        - Damage = (war^2) / (opponent_war + 40) * random(0.75-1.25)
        - War stat is used for damage calculation, stamina is used for HP
        - Fight until someone runs out of stamina or max rounds
        - If lower War defeats higher, winner gains War ability

        Args:
            attacker: Attacking unit (challenger)
            defender: Defending unit (challenged)
            max_rounds: Maximum rounds to fight (default 10)

        Returns:
            Dict with duel results:
            - 'result': 'win', 'loss', or 'draw'
            - 'winner': Winning unit or None
            - 'loser': Losing unit or None
            - 'rounds': List of round results
            - 'war_gained': True if winner gained War ability
            - 'attacker_stamina': Final attacker stamina
            - 'defender_stamina': Final defender stamina
        """
        # Get base War stats (used for damage calculation throughout)
        att_war = attacker.get_war_ability()
        def_war = defender.get_war_ability()

        # Initialize stamina (HP) from War, but track separately
        att_stamina = att_war
        def_stamina = def_war

        rounds = []

        for round_num in range(1, max_rounds + 1):
            # Calculate damage using BASE War stats (not current stamina)
            # ROTK2 damage formula: damage scales with war ratio, max ~14
            # New formula: damage = (war / 8) * (war / (opponent_war + 20)) * random
            # This produces more reasonable damage (typically 3-14)
            att_base = (att_war / 8) * (att_war / (def_war + 20))
            def_base = (def_war / 8) * (def_war / (att_war + 20))

            att_damage = max(1, int(att_base * random.uniform(0.8, 1.2)))
            def_damage = max(1, int(def_base * random.uniform(0.8, 1.2)))

            # Cap damage at 15 to match ROTK2
            att_damage = min(att_damage, 15)
            def_damage = min(def_damage, 15)

            # Apply damage to stamina (HP), not War stat
            att_stamina -= def_damage
            def_stamina -= att_damage

            rounds.append(
                {
                    "round": round_num,
                    "att_damage": att_damage,
                    "def_damage": def_damage,
                    "att_stamina": max(0, att_stamina),
                    "def_stamina": max(0, def_stamina),
                    "att_war": att_war,  # Base War stat (for display)
                    "def_war": def_war,  # Base War stat (for display)
                }
            )

            # Check for winner
            if att_stamina <= 0 or def_stamina <= 0:
                break

        # Determine result
        if att_stamina <= 0 and def_stamina <= 0:
            # Both defeated - draw
            return {
                "result": "draw",
                "winner": None,
                "loser": None,
                "rounds": rounds,
                "war_gained": False,
                "attacker_stamina": 0,
                "defender_stamina": 0,
                "message": "Both warriors fall! The duel ends in a draw.",
            }
        elif att_stamina <= 0:
            # Defender wins
            winner, loser = defender, attacker
        elif def_stamina <= 0:
            # Attacker wins
            winner, loser = attacker, defender
        else:
            # Max rounds reached - draw
            return {
                "result": "draw",
                "winner": None,
                "loser": None,
                "rounds": rounds,
                "war_gained": False,
                "attacker_stamina": max(0, att_stamina),
                "defender_stamina": max(0, def_stamina),
                "message": f"The duel ends after {max_rounds} rounds - neither can overcome the other!",
            }

        # Check for War ability gain (upset victory)
        war_gained = False
        loser_war = loser.get_war_ability()
        winner_war = winner.get_war_ability()

        if loser_war > winner_war:
            # Lower War defeated higher War - gain War ability!
            new_war = (winner_war + loser_war) // 2
            # Note: We can't actually modify the officer here, just report it
            war_gained = True
            war_message = (
                f"{winner.get_officer_name()} gains War ability from the experience!"
            )
        else:
            war_message = ""

        return {
            "result": "win" if winner == attacker else "loss",
            "winner": winner,
            "loser": loser,
            "rounds": rounds,
            "war_gained": war_gained,
            "new_war": (winner_war + loser_war) // 2 if war_gained else winner_war,
            "attacker_stamina": max(0, att_stamina),
            "defender_stamina": max(0, def_stamina),
            "message": f"{winner.get_officer_name()} defeats {loser.get_officer_name()}!",
            "war_message": war_message,
        }

    @staticmethod
    def calculate_refuse_penalty(unit) -> int:
        """
        Calculate desertion penalty for refusing a duel.

        Args:
            unit: Unit that refused the duel

        Returns:
            Number of soldiers that desert
        """
        # ~8% desertion penalty
        base_desertion = int(unit.soldiers * 0.08)
        # Add some randomness
        desertion = max(1, base_desertion + random.randint(-2, 2))
        return min(desertion, unit.soldiers)

    @staticmethod
    def calculate_bribe_success(
        briber_charm: int,
        target_unit,
        gold_offered: int,
    ) -> tuple:
        """
        Calculate bribe success in battle.

        Formula based on ROTK2 mechanics:
        - Defense = (loyalty * 2) / 3 + (honor / 3) + 8
        - If loyalty == 100: defense += 7
        - Defense -= briber_charm / 8
        - Roll = random(0, gold_offered)
        - Success if roll >= defense

        Note: Low honor officers (like Lu Bu, Wei Yan) are naturally easier to bribe
        due to the honor component in the formula. No special cases needed.

        Args:
            briber_charm: Charisma of the officer offering the bribe
            target_unit: The unit being bribed
            gold_offered: Amount of gold (1-99, game caps at 99)

        Returns:
            Tuple of (success: bool, roll: int, defense: int)
        """
        import random

        # Validate gold amount
        if gold_offered < 1 or gold_offered > 99:
            return (False, 0, 999)  # Invalid amount, auto-fail

        # Get target stats
        loyalty = getattr(target_unit.officer, "Loyalty", 50)
        honor = getattr(target_unit.officer, "yili", 50)

        # Calculate defense
        defense = (loyalty * 2) // 3
        if loyalty == 100:
            defense += 7
        defense += honor // 3
        defense += 8

        # Apply briber charm bonus
        defense = max(0, defense - (briber_charm // 8))

        # Roll for success (0 to gold_offered)
        roll = random.randint(0, gold_offered)
        success = roll >= defense

        return (success, roll, defense)

    @staticmethod
    def apply_refuse_penalty_to_side(units: List, side_name: str = "") -> dict:
        """
        Apply 8% desertion penalty to all units on one side for refusing personal combat.

        Args:
            units: List of units to apply penalty to
            side_name: Name of the side (for logging)

        Returns:
            Dict with penalty results
        """
        total_deserted = 0
        result = {"side": side_name, "desertions": [], "total_deserted": 0}

        for unit in units:
            if not unit.is_defeated():
                deserted = CombatSystem.calculate_refuse_penalty(unit)
                unit.soldiers -= deserted
                total_deserted += deserted
                result["desertions"].append(
                    {
                        "unit": unit,
                        "deserted": deserted,
                        "remaining": unit.soldiers,
                    }
                )

        result["total_deserted"] = total_deserted
        return result

    @staticmethod
    def resolve_personal_combat_with_consequences(
        attacker,
        defender,
        battle_engine,
    ) -> dict:
        """
        Resolve personal combat duel and apply all consequences including commander capture.

        This handles the full personal combat resolution including:
        - Duel resolution using resolve_duel()
        - State updates for captured/defeated units
        - Commander capture handling (all units retreat)
        - Victory checking

        Args:
            attacker: Attacking unit (challenger)
            defender: Defending unit (challenged)
            battle_engine: The BattleEngine instance for grid/victory access

        Returns:
            Dict with full combat results:
            - 'duel_result': Original duel result from resolve_duel()
            - 'commander_captured': True if a commander was captured/defeated
            - 'captured_side': "attacker", "defender", or None
            - 'battle_ended': True if battle ended due to commander capture
            - 'victor': "attacker" or "defender" if battle ended
        """
        from .battle_unit import UnitState

        # Resolve the duel
        duel_result = CombatSystem.resolve_duel(attacker, defender)

        # Track results
        result = {
            "duel_result": duel_result,
            "commander_captured": False,
            "captured_side": None,
            "battle_ended": False,
            "victor": None,
        }

        # Apply consequences based on duel outcome
        if duel_result["result"] == "win":
            # Attacker wins - defender captured
            defender.state = UnitState.CAPTURED
            if defender.position:
                battle_engine.grid.remove_unit(defender.position)

            # Check if captured unit was the commander
            if defender.is_commander:
                result["commander_captured"] = True
                result["captured_side"] = "defender"

        elif duel_result["result"] == "loss":
            # Defender wins - attacker defeated
            attacker.state = UnitState.DEFEATED
            if attacker.position:
                battle_engine.grid.remove_unit(attacker.position)

            # Check if defeated unit was the commander
            if attacker.is_commander:
                result["commander_captured"] = True
                result["captured_side"] = "attacker"

        # If commander was captured/defeated, force all units on that side to retreat
        if result["commander_captured"]:
            captured_side = result["captured_side"]

            if captured_side == "attacker":
                units_to_retreat = battle_engine.get_attacking_units_on_map()
                for unit in units_to_retreat:
                    unit.state = UnitState.DEFEATED
                    if unit.position:
                        battle_engine.grid.remove_unit(unit.position)
            else:  # defender
                units_to_retreat = battle_engine.get_defending_units_on_map()
                for unit in units_to_retreat:
                    unit.state = UnitState.CAPTURED
                    if unit.position:
                        battle_engine.grid.remove_unit(unit.position)

            # Check if battle should end
            victory = battle_engine.check_victory()
            if victory:
                result["battle_ended"] = True
                result["victor"] = (
                    "attacker" if captured_side == "defender" else "defender"
                )

        return result


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
