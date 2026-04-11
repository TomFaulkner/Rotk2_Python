"""Shared new-game startup helpers for classic and modern flows."""

from __future__ import annotations

from Data import Data
from Helper import Helper


SCENARIO_RECORD_SIZE = 0x33AF
SCENARIO_COPY_START = 0x42
SCENARIO_COPY_END = 0x33F0
PLAYER_SLOT_OFFSET = 0x3360
START_SEQUENCE_OFFSET = 0x335A + Data.DATA_OFFSET
CURRENT_RULER_OFFSET = 0x335C + Data.DATA_OFFSET
CURRENT_RULER_OFFICER_OFFSET = 0x335E + Data.DATA_OFFSET
CURRENT_PROVINCE_OFFSET = 0x3362 + Data.DATA_OFFSET
GAME_DIFFICULTY_OFFSET = 0x337B + Data.DATA_OFFSET
GAME_OPTIONS_OFFSET = 0x337C + Data.DATA_OFFSET
UNKNOWN_STARTUP_OFFSET_1 = 0x337D + Data.DATA_OFFSET
UNKNOWN_STARTUP_OFFSET_2 = 0x337E + Data.DATA_OFFSET


def load_scenario_into_buffer(scenario_index: int) -> None:
    """Load a scenario record into the legacy runtime buffer."""
    if not 0 <= scenario_index < 6:
        raise ValueError(f"Scenario index out of range: {scenario_index}")

    total_bytes = SCENARIO_COPY_END - SCENARIO_COPY_START
    scenario_offset = scenario_index * SCENARIO_RECORD_SIZE
    Data.BUF[SCENARIO_COPY_START : SCENARIO_COPY_START + total_bytes] = Data.SCENARIO[
        scenario_offset : scenario_offset + total_bytes
    ]


def mark_player_ruler(ruler_no: int, player_number: int = 1) -> None:
    """Mark a ruler as a human player in the legacy startup slots."""
    if not 0 <= ruler_no <= 0x0F:
        raise ValueError(f"Ruler number out of range: {ruler_no}")

    Data.BUF[PLAYER_SLOT_OFFSET + ruler_no] = player_number


def clear_player_rulers() -> None:
    """Clear legacy startup player markers."""
    for i in range(16):
        Data.BUF[PLAYER_SLOT_OFFSET + i] = 0


def initialize_new_game_state(level: int, see_war: int, history: int) -> int:
    """Finalize current ruler/province pointers and game options.

    Returns:
        Selected active ruler number
    """
    year = Data.BUF[0x45] * 256 + Data.BUF[0x44]
    Data.BUF[0x44] = (year + 1) % 256
    Data.BUF[0x45] = int((year + 1) / 256)
    Data.BUF[0x46] = 0

    active_ruler_no = _find_first_player_ruler_no()
    off = Data.RULER_START + active_ruler_no * Data.RULER_SIZE

    Data.BUF[START_SEQUENCE_OFFSET] = 0
    Data.BUF[CURRENT_RULER_OFFSET] = off % 256
    Data.BUF[CURRENT_RULER_OFFSET + 1] = int(off / 256)

    off2 = Data.BUF[off + 1] * 256 + Data.BUF[off]
    Data.BUF[CURRENT_RULER_OFFICER_OFFSET] = off2 % 256
    Data.BUF[CURRENT_RULER_OFFICER_OFFSET + 1] = int(off2 / 256)

    off3 = Data.BUF[off + 3] * 256 + Data.BUF[off + 2]
    Data.BUF[CURRENT_PROVINCE_OFFSET] = off3 % 256
    Data.BUF[CURRENT_PROVINCE_OFFSET + 1] = int(off3 / 256)

    Data.BUF[GAME_DIFFICULTY_OFFSET] = level
    option = 0x0
    option |= see_war
    if history == 1:
        option |= 0x80

    Data.BUF[GAME_OPTIONS_OFFSET] = option
    Data.BUF[UNKNOWN_STARTUP_OFFSET_1] = 5
    Data.BUF[UNKNOWN_STARTUP_OFFSET_2] = 4

    Helper.MainMap = Helper.GetMap()
    return active_ruler_no


def _find_first_player_ruler_no() -> int:
    for i in range(16):
        if Data.BUF[PLAYER_SLOT_OFFSET + i] == 1:
            return i
    raise ValueError("No active player ruler configured in startup slots")
