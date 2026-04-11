"""
Core battle engine.

Manages battle state, turn flow, and victory conditions.
"""

from typing import List, Optional, Dict, Any
from enum import Enum

from .hex_grid import HexGrid, HexCoord
from .battle_unit import BattleUnit, UnitState, ReservePool
from config import get_settings, RiceDepletionMode


class BattlePhase(Enum):
    """Phases of a battle."""

    SETUP = 0  # Unit placement, pre-battle
    DUEL_OFFER = 1  # Day 1: Personal combat challenge
    TACTICAL = 2  # Main battle phase
    REINFORCEMENTS = 3  # Call for reinforcements
    ENDED = 4  # Battle concluded


class BattleResult(Enum):
    """Possible battle outcomes."""

    ATTACKER_WIN = 1
    DEFENDER_WIN = 2
    DRAW = 3
    RETREAT = 4
    CONTINUE = 5


class BattleEngine:
    """
    Main battle engine.

    Manages:
    - Battle grid and terrain
    - Units (attacking and defending)
    - Turn flow
    - Victory conditions
    """

    MAX_UNITS_ON_MAP = 10
    BATTLE_DAYS = 30

    # Weather transition probabilities (ROTK2 accurate)
    WEATHER_TRANSITIONS = {
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

    def __init__(self, province_id: int, is_attacker: bool = True):
        """
        Initialize battle engine.

        Args:
            province_id: Province number (1-41)
            is_attacker: True if player is attacker
        """
        self.province_id = province_id
        self.is_attacker = is_attacker

        # Battle grid
        self.grid = HexGrid()
        self.grid.load_from_province(province_id)

        # Battle state
        self.phase = BattlePhase.SETUP
        self.day = 0
        self.turn = 0  # 0 = attacker, 1 = defender

        # Units
        self.attacking_units: List[BattleUnit] = []
        self.defending_units: List[BattleUnit] = []
        self.attacker_reserve = ReservePool()
        self.defender_reserve = ReservePool()

        # Commanders
        self.attacker_commander: Optional[BattleUnit] = None
        self.defender_commander: Optional[BattleUnit] = None

        # Supplies
        self.attacker_supplies = {"gold": 0, "rice": 0}
        self.defender_supplies = {"gold": 0, "rice": 0}

        # Wind (for fire attacks)
        self.wind_direction: Optional[str] = None  # N, NE, SE, S, SW, NW or None

        # Weather system
        self.weather: str = "sunny"  # sunny, light_clouds, dark_clouds, storm

        # Battle log
        self.log: List[str] = []

        # Active unit
        self.active_unit: Optional[BattleUnit] = None

        # Placement restrictions
        self.attacker_direction: int = 0  # 0-7 (N, NE, E, SE, S, SW, W, NW)
        self.defender_castle_pos: Optional[HexCoord] = None
        self._find_castle()
        self._calculate_attacker_direction()

    def _find_castle(self):
        """Find the main castle hex (code 6) and set as defender base."""
        for coord, hex_obj in self.grid.hexes.items():
            # Code 6 is the main castle
            if hex_obj.terrain_code == 6:
                self.defender_castle_pos = coord
                hex_obj.is_castle = True
                return
            # Fallback: check is_castle flag or CASTLE terrain name
            elif hex_obj.is_castle or (
                hex_obj.terrain.name.lower() == "castle" and not hasattr(hex_obj, "terrain_code")
            ):
                self.defender_castle_pos = coord
                hex_obj.is_castle = True
                return

        # If no castle found, use center of map
        self.defender_castle_pos = HexCoord(self.grid.rows // 2, self.grid.cols // 2)

    def _calculate_attacker_direction(self):
        """
        Calculate which direction attacker came from.

        For now uses a default (South/East side).
        In full game, this would be based on world map direction.
        """
        # Default: attackers come from East (direction 2)
        # Directions: 0=N, 1=NE, 2=E, 3=SE, 4=S, 5=SW, 6=W, 7=NW
        self.attacker_direction = 2

    def get_valid_placement_hexes(self, is_attacker: bool) -> List[HexCoord]:
        """
        Get valid hexes for unit placement.

        Args:
            is_attacker: True for attacker placement zones

        Returns:
            List of valid HexCoord for placement
        """
        valid_hexes = []

        if is_attacker:
            # Attackers place on edges based on their direction
            valid_hexes = self._get_attacker_placement_zones()
        else:
            # Defenders place within radius of castle
            valid_hexes = self._get_defender_placement_zones()

        return valid_hexes

    def _get_attacker_placement_zones(self) -> List[HexCoord]:
        """
        Get valid placement zones for attackers.

        Attackers can only place on the edge they entered from.
        """
        valid = []

        # Direction to edge mapping
        # 0=N (top), 1=NE (top-right), 2=E (right), 3=SE (bottom-right)
        # 4=S (bottom), 5=SW (bottom-left), 6=W (left), 7=NW (top-left)
        direction_edges = {
            0: [(0, c) for c in range(self.grid.cols)],  # North edge
            1: [(0, c) for c in range(self.grid.cols // 2, self.grid.cols)]
            + [(1, c) for c in range(self.grid.cols // 2, self.grid.cols)],
            2: [(r, self.grid.cols - 1) for r in range(self.grid.rows)],  # East edge
            3: [(r, self.grid.cols - 1) for r in range(self.grid.rows // 2, self.grid.rows)]
            + [(r, self.grid.cols - 2) for r in range(self.grid.rows // 2, self.grid.rows)],
            4: [(self.grid.rows - 1, c) for c in range(self.grid.cols)],  # South edge
            5: [(r, 0) for r in range(self.grid.rows // 2, self.grid.rows)]
            + [(r, 1) for r in range(self.grid.rows // 2, self.grid.rows)],
            6: [(r, 0) for r in range(self.grid.rows)],  # West edge
            7: [(0, c) for c in range(self.grid.cols // 2)]
            + [(1, c) for c in range(self.grid.cols // 2)],
        }

        edge_positions = direction_edges.get(self.attacker_direction, direction_edges[2])

        for row, col in edge_positions:
            coord = HexCoord(row, col)
            hex_obj = self.grid.get_hex(coord)
            if hex_obj and hex_obj.is_passable() and not hex_obj.unit:
                valid.append(coord)

        return valid

    def _get_defender_placement_zones(self) -> List[HexCoord]:
        """
        Get valid placement zones for defenders.

        Defenders can place within 3 hexes of their castle.
        """
        valid = []

        if not self.defender_castle_pos:
            return valid

        # Check all hexes within radius 3 of castle
        for coord, hex_obj in self.grid.hexes.items():
            # Calculate distance (rough hex distance)
            row_diff = abs(coord.row - self.defender_castle_pos.row)
            col_diff = abs(coord.col - self.defender_castle_pos.col)
            # Hex distance approximation
            distance = max(row_diff, col_diff // 2 + row_diff // 2)

            if distance <= 3:
                if hex_obj.is_passable() and not hex_obj.unit:
                    valid.append(coord)

        return valid

    def is_valid_placement(self, coord: HexCoord, is_attacker: bool) -> bool:
        """
        Check if placement at coordinate is valid.

        Args:
            coord: Position to check
            is_attacker: True if checking for attacker

        Returns:
            True if valid placement
        """
        valid_hexes = self.get_valid_placement_hexes(is_attacker)
        return coord in valid_hexes

    def add_attacking_unit(self, unit: BattleUnit, to_reserve: bool = False):
        """
        Add attacking unit to battle.

        Args:
            unit: Unit to add
            to_reserve: True to put in reserve, False for battlefield
        """
        unit.is_attacker = True
        if to_reserve or len(self.get_attacking_units_on_map()) >= self.MAX_UNITS_ON_MAP:
            self.attacker_reserve.add(unit)
        else:
            self.attacking_units.append(unit)
            unit.state = UnitState.INACTIVE

    def add_defending_unit(self, unit: BattleUnit, to_reserve: bool = False):
        """
        Add defending unit to battle.

        Args:
            unit: Unit to add
            to_reserve: True to put in reserve, False for battlefield
        """
        unit.is_attacker = False
        if to_reserve or len(self.get_defending_units_on_map()) >= self.MAX_UNITS_ON_MAP:
            self.defender_reserve.add(unit)
        else:
            self.defending_units.append(unit)
            unit.state = UnitState.INACTIVE

    def get_attacking_units_on_map(self) -> List[BattleUnit]:
        """
        Get all attacking units currently on the battlefield.

        Returns:
            List of attacking units
        """
        return [
            u
            for u in self.attacking_units
            if u.state
            not in [
                UnitState.DEFEATED,
                UnitState.CAPTURED,
                UnitState.IN_RESERVE,
                UnitState.INACTIVE,
            ]
        ]

    def get_defending_units_on_map(self) -> List[BattleUnit]:
        """
        Get all defending units currently on the battlefield.

        Returns:
            List of defending units
        """
        return [
            u
            for u in self.defending_units
            if u.state
            not in [
                UnitState.DEFEATED,
                UnitState.CAPTURED,
                UnitState.IN_RESERVE,
                UnitState.INACTIVE,
            ]
        ]

    def get_all_units_on_map(self) -> List[BattleUnit]:
        """
        Get all units on the battlefield.

        Returns:
            List of all active units
        """
        return self.get_attacking_units_on_map() + self.get_defending_units_on_map()

    def set_commander(self, unit: BattleUnit, is_attacker: bool):
        """
        Set commander for a side.

        Args:
            unit: Unit to be commander
            is_attacker: True for attacker commander, False for defender
        """
        unit.set_commander(True)
        if is_attacker:
            self.attacker_commander = unit
        else:
            self.defender_commander = unit

    def place_unit(self, unit: BattleUnit, coord: HexCoord) -> bool:
        """
        Place a unit on the battlefield.

        Args:
            unit: Unit to place
            coord: Position to place at

        Returns:
            True if successful
        """
        if not self.grid.place_unit(unit, coord):
            return False

        unit.state = UnitState.ACTIVE
        self.log.append(f"{unit.get_officer_name()} placed at {coord}")
        return True

    def call_reinforcements(self, is_attacker: bool) -> List[BattleUnit]:
        """
        Call reinforcements from reserve.

        Args:
            is_attacker: True for attacker reinforcements

        Returns:
            List of units called from reserve
        """
        reserve = self.attacker_reserve if is_attacker else self.defender_reserve
        current_count = len(
            self.get_attacking_units_on_map() if is_attacker else self.get_defending_units_on_map()
        )

        called = []
        available = reserve.get_available()

        while current_count < self.MAX_UNITS_ON_MAP and available:
            unit = available.pop(0)
            reserve.remove(unit)

            if is_attacker:
                self.attacking_units.append(unit)
            else:
                self.defending_units.append(unit)

            unit.state = UnitState.INACTIVE
            called.append(unit)
            current_count += 1

        if called:
            side = "Attacker" if is_attacker else "Defender"
            self.log.append(f"{side} called {len(called)} reinforcements")

        return called

    def check_victory(self) -> Optional[BattleResult]:
        """
        Check if victory conditions are met.

        Returns:
            BattleResult if battle ended, None if continues
        """
        attacker_units = self.get_attacking_units_on_map()
        defender_units = self.get_defending_units_on_map()

        # Check commander capture/death
        if self.attacker_commander and self.attacker_commander.is_defeated():
            self.log.append("Attacker commander defeated! Defender wins!")
            return BattleResult.DEFENDER_WIN

        if self.defender_commander and self.defender_commander.is_defeated():
            self.log.append("Defender commander defeated! Attacker wins!")
            return BattleResult.ATTACKER_WIN

        # Check for no units
        if not attacker_units:
            self.log.append("No attacking units remaining! Defender wins!")
            return BattleResult.DEFENDER_WIN

        if not defender_units:
            self.log.append("No defending units remaining! Attacker wins!")
            return BattleResult.ATTACKER_WIN

        return None

    def calculate_daily_rice_consumption(self, total_troops: int) -> int:
        """
        Calculate daily rice consumption for battle.

        Formula: total_troops // consumption_rate (default: 250, i.e., 4 rice per 1,000 troops)

        Args:
            total_troops: Total number of troops

        Returns:
            Rice consumed
        """
        settings = get_settings()
        return total_troops // settings.rice_consumption_rate

    def consume_rice_and_handle_depletion(self, is_attacker: bool) -> dict:
        """
        Consume rice for a side and handle depletion based on configured mode.

        Modes:
        - force_retreat: Original game behavior, force full retreat when rice runs out
        - desertion: Alternative mode, 15% of troops desert daily when out of rice

        Args:
            is_attacker: True for attacker, False for defender

        Returns:
            Dict with consumption info and depletion results
        """
        settings = get_settings()
        units = (
            self.get_attacking_units_on_map() if is_attacker else self.get_defending_units_on_map()
        )
        total_troops = sum(unit.soldiers for unit in units)

        if is_attacker:
            rice_key = "attacker_supplies"
            side_name = "Attacker"
        else:
            rice_key = "defender_supplies"
            side_name = "Defender"

        supplies = getattr(self, rice_key)
        consumption = self.calculate_daily_rice_consumption(total_troops)

        result = {
            "side": side_name,
            "troops": total_troops,
            "consumption": consumption,
            "previous_rice": supplies["rice"],
            "out_of_rice": False,
            "forced_retreat": False,
            "desertion": 0,
        }

        # Check if already out of rice (for desertion mode - daily desertion)
        if supplies["rice"] <= 0:
            result["out_of_rice"] = True
            supplies["rice"] = 0  # Keep at 0

            if settings.rice_depletion_mode == RiceDepletionMode.DESERTION:
                # Desertion mode: Continue losing troops daily while out of rice
                desertion = int(total_troops * settings.desertion_percentage)
                result["desertion"] = desertion
                result["forced_retreat"] = False

                # Apply desertion to units proportionally
                if desertion > 0 and units:
                    troops_per_unit = desertion // len(units)
                    for unit in units:
                        unit.soldiers = max(0, unit.soldiers - troops_per_unit)
                        if unit.soldiers == 0:
                            unit.state = UnitState.DEFEATED
                            if unit.position:
                                self.grid.remove_unit(unit.position)

                    self.log.append(f"{side_name} out of rice! {desertion} more troops deserted!")
            else:
                # Force retreat mode: Apply retreat if units still present
                # This handles cases where rice started at 0 or previous retreat didn't clear units
                if units:
                    result["forced_retreat"] = True
                    self.log.append(f"{side_name} has no rice! Forced to retreat!")

                    # Mark all units as defeated/retreated
                    for unit in units:
                        unit.state = UnitState.DEFEATED
                        if unit.position:
                            self.grid.remove_unit(unit.position)

            return result

        # Deduct rice
        supplies["rice"] -= consumption

        # Check for rice depletion (first time running out)
        if supplies["rice"] < 0:
            supplies["rice"] = 0
            result["out_of_rice"] = True

            if settings.rice_depletion_mode == RiceDepletionMode.FORCE_RETREAT:
                # Original game behavior: Force full retreat
                result["forced_retreat"] = True
                self.log.append(f"{side_name} ran out of rice! Forced to retreat!")

                # Mark all units as defeated/retreated
                for unit in units:
                    unit.state = UnitState.DEFEATED
                    if unit.position:
                        self.grid.remove_unit(unit.position)

            else:  # Desertion mode - first day out of rice
                # Alternative: 15% of troops desert when out of rice
                desertion = int(total_troops * settings.desertion_percentage)
                result["desertion"] = desertion

                # Apply desertion to units proportionally
                if desertion > 0 and units:
                    troops_per_unit = desertion // len(units)
                    for unit in units:
                        unit.soldiers = max(0, unit.soldiers - troops_per_unit)
                        if unit.soldiers == 0:
                            unit.state = UnitState.DEFEATED
                            if unit.position:
                                self.grid.remove_unit(unit.position)

                    self.log.append(f"{side_name} ran out of rice! {desertion} troops deserted!")

        return result

    def next_turn(self) -> bool:
        """
        Advance to next turn.

        Returns:
            True if battle continues, False if ended
        """
        # Check victory
        result = self.check_victory()
        if result:
            self.phase = BattlePhase.ENDED
            return False

        # Advance day and consume rice
        if self.turn == 1:  # After defender's turn
            self.day += 1

            # Consume rice for both sides
            attacker_result = self.consume_rice_and_handle_depletion(True)
            defender_result = self.consume_rice_and_handle_depletion(False)

            # Log rice consumption
            self.log.append(f"Day {self.day} rice consumption:")
            self.log.append(
                f"  Attacker: {attacker_result['consumption']} rice ({attacker_result['troops']} troops)"
            )
            self.log.append(
                f"  Defender: {defender_result['consumption']} rice ({defender_result['troops']} troops)"
            )

            # Check for out of rice and log appropriately
            if attacker_result["out_of_rice"]:
                if attacker_result["forced_retreat"]:
                    self.log.append(f"  *** ATTACKER OUT OF RICE - FORCED TO RETREAT! ***")
                else:
                    self.log.append(
                        f"  *** ATTACKER OUT OF RICE - {attacker_result['desertion']} troops deserted! ***"
                    )
            if defender_result["out_of_rice"]:
                if defender_result["forced_retreat"]:
                    self.log.append(f"  *** DEFENDER OUT OF RICE - FORCED TO RETREAT! ***")
                else:
                    self.log.append(
                        f"  *** DEFENDER OUT OF RICE - {defender_result['desertion']} troops deserted! ***"
                    )

            # Check victory again in case rice depletion caused retreat
            result = self.check_victory()
            if result:
                self.phase = BattlePhase.ENDED
                return False

        # Switch turn
        self.turn = 1 - self.turn

        # Reset unit states for new turn
        for unit in self.get_all_units_on_map():
            unit.end_turn()

        return True

    def transition_weather(self) -> str:
        """
        Transition weather based on ROTK2 probability matrix.
        Called automatically at the start of each day.

        Returns:
            New weather state
        """
        import random

        transitions = self.WEATHER_TRANSITIONS.get(self.weather, self.WEATHER_TRANSITIONS["sunny"])

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
            for coord, hex_obj in self.grid.hexes.items():
                if hex_obj.is_burning:
                    hex_obj.extinguish()
                    extinguished.append(coord)
            if extinguished:
                self.log.append(f">>> Storm extinguishes all {len(extinguished)} fires!")

        self.weather = new_weather
        return new_weather

    def process_daily_fire_effects(self) -> dict:
        """
        Process fire effects at the start of each day.
        - Spread/extinguish fires based on wind and weather
        - Apply fire damage to units on burning hexes

        Returns:
            Dict with fire processing results
        """
        from .combat_system import CombatSystem
        import random

        result = {
            "new_fires": [],
            "extinguished": [],
            "fire_damage": [],
        }

        # Process fire spread/extinguish
        new_fires, extinguished = CombatSystem.process_fires(
            self.grid, self.wind_direction, self.weather
        )

        result["new_fires"] = new_fires
        result["extinguished"] = extinguished

        # Units on burning hexes take damage
        for unit in self.get_all_units_on_map():
            if unit.position:
                hex_obj = self.grid.get_hex(unit.position)
                if hex_obj and hex_obj.is_burning:
                    fire_damage = 10 + random.randint(0, 10)
                    casualties = unit.take_damage(fire_damage)
                    result["fire_damage"].append(
                        {
                            "unit": unit,
                            "damage": fire_damage,
                            "casualties": casualties,
                            "defeated": unit.is_defeated(),
                        }
                    )
                    if unit.is_defeated():
                        self.grid.remove_unit(unit.position)

        return result

    def validate_placement_and_start(self) -> dict:
        """
        Validate placement requirements and start the battle if valid.

        Requirements:
        - Defender must have placed their commander
        - Attacker must have placed ALL their units

        Returns:
            Dict with validation results:
            - 'valid': True if can start battle
            - 'error': Error message if invalid
            - 'phase': New phase if valid ("personal_combat_offer")
        """
        result = {"valid": False, "error": None, "phase": None}

        # Defender must have placed their commander
        defender_units_on_map = self.get_defending_units_on_map()
        defender_commander_placed = any(u.is_commander for u in defender_units_on_map)

        if not defender_commander_placed:
            result["error"] = "Defender must place their commander!"
            return result

        # Attacker must have placed ALL their units
        attacker_units_on_map = self.get_attacking_units_on_map()
        total_attacker_units = len(self.attacking_units)

        if len(attacker_units_on_map) < total_attacker_units:
            unplaced = total_attacker_units - len(attacker_units_on_map)
            result["error"] = (
                f"Attacker must place all {total_attacker_units} units! ({unplaced} remaining)"
            )
            return result

        # All requirements met - start the battle
        self.phase = BattlePhase.DUEL_OFFER
        result["valid"] = True
        result["phase"] = "personal_combat_offer"

        return result

    def get_current_side_units(self) -> List[BattleUnit]:
        """
        Get units for current turn's side.

        Returns:
            List of units for current player
        """
        if self.turn == 0:
            return self.get_attacking_units_on_map()
        else:
            return self.get_defending_units_on_map()

    def log_action(self, message: str):
        """
        Log a battle action.

        Args:
            message: Message to log
        """
        self.log.append(f"Day {self.day}: {message}")

    def get_battle_summary(self) -> Dict[str, Any]:
        """
        Get summary of battle state.

        Returns:
            Dictionary with battle info
        """
        return {
            "province_id": self.province_id,
            "day": self.day,
            "phase": self.phase.name,
            "turn": "Attacker" if self.turn == 0 else "Defender",
            "attacker_units": len(self.get_attacking_units_on_map()),
            "defender_units": len(self.get_defending_units_on_map()),
            "attacker_reserve": len(self.attacker_reserve),
            "defender_reserve": len(self.defender_reserve),
        }

    def __repr__(self) -> str:
        """String representation."""
        return f"BattleEngine(Province {self.province_id}, Day {self.day})"
