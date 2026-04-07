"""
Battle module for ROTK2.

This module contains all battle-related classes and functionality.
"""

from .hex_grid import HexGrid, HexCoord, TerrainType
from .battle_unit import BattleUnit, UnitState, ReservePool
from .terrain import Terrain
from .battle_engine import BattleEngine, BattlePhase, BattleResult
from .turn_manager import TurnManager, TurnPhase
from .battle_ui import BattleUI, BattlePhaseUI
from .battle_game import BattleGame, BattleGamePhase

__all__ = [
    "HexGrid",
    "HexCoord",
    "TerrainType",
    "BattleUnit",
    "UnitState",
    "ReservePool",
    "Terrain",
    "BattleEngine",
    "BattlePhase",
    "BattleResult",
    "TurnManager",
    "TurnPhase",
    "BattleUI",
    "BattlePhaseUI",
    "BattleGame",
    "BattleGamePhase",
]
