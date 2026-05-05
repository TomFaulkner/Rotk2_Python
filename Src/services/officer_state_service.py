"""Runtime-only officer state not represented directly in Data.BUF."""

from __future__ import annotations

from Officer import Officer
from Data import Data


_years_of_service_by_officer: dict[int, int] = {}
_current_ruler_by_officer: dict[int, int] = {}
_reward_item_rulers_by_officer: dict[int, set[int]] = {}
_special_items_by_officer: dict[int, list[str]] = {}
_has_horse_by_officer: dict[int, bool] = {}


def initialize_runtime_state() -> None:
    """Initialize runtime-only officer tracking for a fresh game state."""
    _years_of_service_by_officer.clear()
    _current_ruler_by_officer.clear()
    _reward_item_rulers_by_officer.clear()
    _special_items_by_officer.clear()
    _has_horse_by_officer.clear()

    for index in range(Data.MaxNumberOfGenerals):
        offset = Data.OFFICER_START + index * Data.OFFICER_SIZE
        officer = Officer.FromOffset(offset)
        if officer is None:
            continue
        _current_ruler_by_officer[offset] = officer.RulerNo
        _years_of_service_by_officer[offset] = 1 if officer.RulerNo != 0xFF else 0
        _reward_item_rulers_by_officer[offset] = set()
        _special_items_by_officer[offset] = []
        _has_horse_by_officer[offset] = False


def _ensure_officer_initialized(officer: Officer) -> None:
    """Ensure runtime tracking exists for an officer."""
    if officer.Offset not in _current_ruler_by_officer:
        _current_ruler_by_officer[officer.Offset] = officer.RulerNo
        _years_of_service_by_officer[officer.Offset] = 1 if officer.RulerNo != 0xFF else 0
    _reward_item_rulers_by_officer.setdefault(officer.Offset, set())
    _special_items_by_officer.setdefault(officer.Offset, [])
    _has_horse_by_officer.setdefault(officer.Offset, False)


def synchronize_officer_ruler_state() -> None:
    """Reset current-ruler-dependent runtime state when officers change rulers."""
    for index in range(Data.MaxNumberOfGenerals):
        offset = Data.OFFICER_START + index * Data.OFFICER_SIZE
        officer = Officer.FromOffset(offset)
        if officer is None:
            continue

        previous_ruler_no = _current_ruler_by_officer.get(offset)
        if previous_ruler_no is None:
            _ensure_officer_initialized(officer)
            continue

        if previous_ruler_no == officer.RulerNo:
            continue

        _current_ruler_by_officer[offset] = officer.RulerNo
        _years_of_service_by_officer[offset] = 1 if officer.RulerNo != 0xFF else 0
        _reward_item_rulers_by_officer.setdefault(offset, set())


def increment_years_of_service() -> None:
    """Increase years of service for officers currently serving a ruler."""
    synchronize_officer_ruler_state()
    for index in range(Data.MaxNumberOfGenerals):
        offset = Data.OFFICER_START + index * Data.OFFICER_SIZE
        officer = Officer.FromOffset(offset)
        if officer is None or officer.RulerNo == 0xFF:
            continue
        _ensure_officer_initialized(officer)
        _years_of_service_by_officer[offset] = max(1, _years_of_service_by_officer[offset] + 1)


def get_years_of_service(officer: Officer) -> int:
    """Return years served under the officer's current ruler."""
    _ensure_officer_initialized(officer)
    if _current_ruler_by_officer.get(officer.Offset) != officer.RulerNo:
        _current_ruler_by_officer[officer.Offset] = officer.RulerNo
        _years_of_service_by_officer[officer.Offset] = 1 if officer.RulerNo != 0xFF else 0
    return _years_of_service_by_officer.get(officer.Offset, 0)


def mark_rewarded_item(officer: Officer, ruler_no: int | None = None) -> None:
    """Record that a ruler has rewarded this officer with a special gifted item.

    This is for unique battle-found items, not regular gold/horse/book rewards.
    """
    _ensure_officer_initialized(officer)
    target_ruler_no = officer.RulerNo if ruler_no is None else ruler_no
    if target_ruler_no == 0xFF:
        return
    _reward_item_rulers_by_officer[officer.Offset].add(target_ruler_no)


def get_rewarded_item_ruler_history(officer: Officer) -> tuple[int, ...]:
    """Return the sorted tuple of rulers who have rewarded this officer with an item."""
    _ensure_officer_initialized(officer)
    return tuple(sorted(_reward_item_rulers_by_officer.get(officer.Offset, set())))


def assign_special_item(
    officer: Officer,
    item_name: str,
    ruler_no: int | None = None,
    grants_horse: bool = False,
) -> None:
    """Attach a special item to the officer and record current-ruler item protection."""
    _ensure_officer_initialized(officer)
    if item_name not in _special_items_by_officer[officer.Offset]:
        _special_items_by_officer[officer.Offset].append(item_name)
    if grants_horse:
        _has_horse_by_officer[officer.Offset] = True
    mark_rewarded_item(officer, ruler_no)


def get_special_items(officer: Officer) -> tuple[str, ...]:
    """Return the officer's assigned special items."""
    _ensure_officer_initialized(officer)
    return tuple(_special_items_by_officer.get(officer.Offset, []))


def has_horse(officer: Officer) -> bool:
    """Return True when the officer owns a capture-immune horse item."""
    _ensure_officer_initialized(officer)
    return _has_horse_by_officer.get(officer.Offset, False)


def has_item_reward_from_current_ruler(officer: Officer) -> bool:
    """Return True if the officer has received an item from the current ruler."""
    if officer.RulerNo == 0xFF:
        return False
    _ensure_officer_initialized(officer)
    return officer.RulerNo in _reward_item_rulers_by_officer.get(officer.Offset, set())
