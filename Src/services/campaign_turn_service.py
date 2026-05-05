"""Campaign turn progression helpers for the modern province hub."""

from __future__ import annotations

from dataclasses import dataclass

from Data import Data, DelegateMode
from Helper import Helper
from Province import Province
from Ruler import Ruler
from officer_display import get_officer_display_name
from . import month_transition_service
from . import peaceful_ai_service
from . import province_command_service as province_service


TURN_SEQUENCE_OFFSET = 0x335A + Data.DATA_OFFSET
PLAYER_SEQUENCE_OFFSET = 0x3360
ORDERED_RULER_CACHE_OFFSET = 0x3370
MONTH_NAMES = [
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
]


@dataclass(frozen=True)
class TurnAdvanceResult:
    """Structured result for campaign turn progression."""

    kind: str
    current_ruler_no: int
    next_ruler_no: int
    current_province_no: int
    next_province_no: int
    year: int
    month: int
    is_human_ruler: bool
    message: str = ""


def get_current_turn_ruler_index() -> int:
    """Return the zero-based ruler turn-order index currently being processed."""
    return Data.BUF[TURN_SEQUENCE_OFFSET]


def set_current_turn_ruler_index(index: int) -> None:
    """Set the zero-based ruler turn-order index currently being processed."""
    Data.BUF[TURN_SEQUENCE_OFFSET] = max(0, index) % 256


def _get_current_year() -> int:
    return Data.BUF[0x44] + Data.BUF[0x45] * 256


def _get_current_month() -> int:
    return Data.BUF[0x46]


def _get_month_name(month_zero_based: int) -> str:
    if 0 <= month_zero_based < len(MONTH_NAMES):
        return MONTH_NAMES[month_zero_based]
    return str(month_zero_based + 1)


def is_human_ruler(ruler_no: int) -> bool:
    """Return True when the ruler is configured as a human player."""
    if not 0 <= ruler_no < 16:
        return False
    return Data.BUF[PLAYER_SEQUENCE_OFFSET + ruler_no] > 0


def is_delegated_province(province_no: int) -> bool:
    """Return True when a province is delegated to its governor."""
    return Province.GetDelegateStatus(province_no) != DelegateMode.No


def get_turn_provinces_for_ruler(
    ruler_no: int, allow_delegated_fallback: bool = False
) -> list[Province]:
    """Return the provinces a ruler should manually visit this turn."""
    provinces = province_service.get_ruler_provinces(ruler_no)
    if not is_human_ruler(ruler_no):
        return provinces

    direct_control = [province for province in provinces if not is_delegated_province(province.No)]
    if direct_control or not allow_delegated_fallback:
        return direct_control
    return provinces


def get_ordered_ruler_nos() -> list[int]:
    """Return rulers in the cached monthly play order."""
    offset_to_no = {ruler.Offset: ruler.No for ruler in Ruler.GetList()}
    ordered: list[int] = []
    for index in range(16):
        ruler_offset = Data.GetWordFromOffset(Data.BUF, ORDERED_RULER_CACHE_OFFSET + index * 2)
        if ruler_offset == 0:
            continue
        ruler_no = offset_to_no.get(ruler_offset)
        if ruler_no is None or ruler_no in ordered:
            continue
        ordered.append(ruler_no)

    if ordered:
        return ordered

    Helper.GetRulersOrder()
    offset_to_no = {ruler.Offset: ruler.No for ruler in Ruler.GetList()}
    for index in range(16):
        ruler_offset = Data.GetWordFromOffset(Data.BUF, ORDERED_RULER_CACHE_OFFSET + index * 2)
        if ruler_offset == 0:
            continue
        ruler_no = offset_to_no.get(ruler_offset)
        if ruler_no is None or ruler_no in ordered:
            continue
        ordered.append(ruler_no)
    return ordered


def set_active_ruler_no(ruler_no: int) -> Ruler:
    """Set the active ruler and ruler-officer pointers."""
    ruler = Ruler.FromNo(ruler_no)
    Data.SetWordToOffset(Data.BUF, ruler.Offset, Data.CURRENT_RULER_OFFSET)
    ruler_officer_offset = ruler.RulerSelf.Offset if ruler and ruler.RulerSelf else 0
    Data.SetWordToOffset(Data.BUF, ruler_officer_offset, Data.CURRENT_RULER_OFFICER_OFFSET)
    return ruler


def _set_active_ruler_and_first_province(
    ruler_no: int, allow_delegated_fallback: bool = False
) -> tuple[Ruler, Province]:
    """Set active pointers to a ruler and that ruler's first owned province."""
    ruler = set_active_ruler_no(ruler_no)
    provinces = get_turn_provinces_for_ruler(ruler_no, allow_delegated_fallback)
    if not provinces:
        raise ValueError(f"Ruler {ruler_no} has no provinces to activate")
    province = province_service.set_active_province_no(provinces[0].No)
    return ruler, province


def _advance_to_next_turn_province(current_ruler_no: int, current_province_no: int) -> int | None:
    """Advance to the next manually controlled province for the active ruler."""
    provinces = get_turn_provinces_for_ruler(current_ruler_no)
    if not provinces:
        return None

    province_numbers = [province.No for province in provinces]
    if current_province_no not in province_numbers:
        next_province = province_service.set_active_province_no(province_numbers[0])
        return next_province.No

    current_index = province_numbers.index(current_province_no)
    if current_index + 1 >= len(province_numbers):
        return None

    next_province = province_service.set_active_province_no(province_numbers[current_index + 1])
    return next_province.No


def reset_monthly_officer_actions() -> None:
    """Clear the monthly action-used bit for all officer records."""
    month_transition_service.reset_monthly_officer_actions()


def advance_month() -> tuple[int, int]:
    """Advance the in-game month and clear monthly officer actions."""
    summary = month_transition_service.process_month_transition()
    return summary.year, summary.month


def _run_peaceful_automation_until_next_human(
    ordered_ruler_nos: list[int], start_index: int
) -> tuple[int, int] | None:
    """Run peaceful automation for later rulers until the next human ruler is found."""
    for index in range(start_index + 1, len(ordered_ruler_nos)):
        ruler_no = ordered_ruler_nos[index]
        peaceful_ai_service.run_peaceful_turn_for_ruler(ruler_no)
        if is_human_ruler(ruler_no) and get_turn_provinces_for_ruler(ruler_no):
            return index, ruler_no
    return None


def _get_transition_message(ruler: Ruler, province: Province, include_date: bool = False) -> str:
    """Build a simple prompt override for ruler/month transitions."""
    ruler_name = (
        get_officer_display_name(ruler.RulerSelf) if ruler and ruler.RulerSelf else "Commander"
    )
    base = f"{ruler_name}, your turn begins in Province {province.No}."
    if not include_date:
        return base
    return f"{_get_month_name(_get_current_month())} {_get_current_year()}. {base}"


def _find_order_index(ordered_ruler_nos: list[int], current_ruler_no: int) -> int:
    """Return the best-known turn-order index for the current ruler."""
    current_index = get_current_turn_ruler_index()
    if (
        0 <= current_index < len(ordered_ruler_nos)
        and ordered_ruler_nos[current_index] == current_ruler_no
    ):
        return current_index
    if current_ruler_no in ordered_ruler_nos:
        current_index = ordered_ruler_nos.index(current_ruler_no)
        set_current_turn_ruler_index(current_index)
        return current_index
    set_current_turn_ruler_index(0)
    return 0


def _find_first_human_ruler(
    ordered_ruler_nos: list[int], allow_delegated_fallback: bool = False
) -> tuple[int, int] | None:
    """Return the first human ruler in monthly order."""
    for index, ruler_no in enumerate(ordered_ruler_nos):
        if not is_human_ruler(ruler_no):
            continue
        if not get_turn_provinces_for_ruler(ruler_no, allow_delegated_fallback):
            continue
        return index, ruler_no
    return None


def advance_campaign_turn() -> TurnAdvanceResult:
    """Advance to the next province, next human ruler, or next month."""
    current_ruler_no = province_service.get_active_ruler_no()
    current_province_no = province_service.get_active_province_no()

    next_province_no = _advance_to_next_turn_province(current_ruler_no, current_province_no)
    if next_province_no is not None:
        message = ""
        if is_human_ruler(current_ruler_no) and is_delegated_province(current_province_no):
            message = f"Province {current_province_no} is delegated. Continuing with Province {next_province_no}."
        return TurnAdvanceResult(
            kind="province",
            current_ruler_no=current_ruler_no,
            next_ruler_no=current_ruler_no,
            current_province_no=current_province_no,
            next_province_no=next_province_no,
            year=_get_current_year(),
            month=_get_current_month(),
            is_human_ruler=is_human_ruler(current_ruler_no),
            message=message,
        )

    ordered_ruler_nos = get_ordered_ruler_nos()
    current_index = _find_order_index(ordered_ruler_nos, current_ruler_no)
    next_human = _run_peaceful_automation_until_next_human(ordered_ruler_nos, current_index)

    if next_human is not None:
        next_index, next_ruler_no = next_human
        set_current_turn_ruler_index(next_index)
        ruler, province = _set_active_ruler_and_first_province(next_ruler_no)
        return TurnAdvanceResult(
            kind="ruler",
            current_ruler_no=current_ruler_no,
            next_ruler_no=next_ruler_no,
            current_province_no=current_province_no,
            next_province_no=province.No,
            year=_get_current_year(),
            month=_get_current_month(),
            is_human_ruler=True,
            message=_get_transition_message(ruler, province),
        )

    year, month = advance_month()
    ordered_ruler_nos = get_ordered_ruler_nos()
    first_human = _run_peaceful_automation_until_next_human(ordered_ruler_nos, -1)
    if first_human is not None:
        next_index, next_ruler_no = first_human
        set_current_turn_ruler_index(next_index)
        ruler, province = _set_active_ruler_and_first_province(next_ruler_no)
        return TurnAdvanceResult(
            kind="month",
            current_ruler_no=current_ruler_no,
            next_ruler_no=next_ruler_no,
            current_province_no=current_province_no,
            next_province_no=province.No,
            year=year,
            month=month,
            is_human_ruler=True,
            message=_get_transition_message(ruler, province, include_date=True),
        )

    fallback_human = _find_first_human_ruler(ordered_ruler_nos, allow_delegated_fallback=True)
    if fallback_human is not None:
        next_index, fallback_ruler_no = fallback_human
        set_current_turn_ruler_index(next_index)
        ruler, province = _set_active_ruler_and_first_province(
            fallback_ruler_no, allow_delegated_fallback=True
        )
        return TurnAdvanceResult(
            kind="month",
            current_ruler_no=current_ruler_no,
            next_ruler_no=fallback_ruler_no,
            current_province_no=current_province_no,
            next_province_no=province.No,
            year=year,
            month=month,
            is_human_ruler=True,
            message=_get_transition_message(ruler, province, include_date=True),
        )

    fallback_ruler_no = ordered_ruler_nos[0] if ordered_ruler_nos else current_ruler_no
    set_current_turn_ruler_index(0)
    ruler, province = _set_active_ruler_and_first_province(
        fallback_ruler_no, allow_delegated_fallback=True
    )
    return TurnAdvanceResult(
        kind="month",
        current_ruler_no=current_ruler_no,
        next_ruler_no=fallback_ruler_no,
        current_province_no=current_province_no,
        next_province_no=province.No,
        year=year,
        month=month,
        is_human_ruler=is_human_ruler(fallback_ruler_no),
        message=_get_transition_message(ruler, province, include_date=True),
    )
