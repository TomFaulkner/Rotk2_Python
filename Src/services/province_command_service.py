"""Small service boundary for modern province command UI."""

from __future__ import annotations

from dataclasses import dataclass
import math
import random

from Officer import Officer
from Province import Province
from Ruler import Ruler
from officer_display import get_officer_display_name
from Data import Data
from config import get_settings


@dataclass(frozen=True)
class OfficerRow:
    """UI-ready officer row data for modern list screens."""

    officer: Officer
    name: str
    loyalty: int
    intelligence: int
    war: int
    charm: int
    service: int
    soldiers: int
    arms: int
    training: int


@dataclass(frozen=True)
class TerritoryRow:
    """UI-ready territory row data for the territory overview."""

    province_no: int
    province_name: str
    governor_name: str
    gold: int
    rice: int
    soldiers: int
    general_count: int
    loyalty: int


@dataclass(frozen=True)
class InternalActionEstimate:
    """Calculated result for an internal-affairs action before or after apply."""

    province_no: int
    officer: Officer
    officer_name: str
    officer_count: int
    action_name: str
    cost_field: str
    cost_amount: int
    current_value: int
    projected_gain: int
    projected_value: int


@dataclass(frozen=True)
class AdvisorOpinion:
    """Advisor prediction for an internal-affairs action."""

    advisor: Officer
    advisor_name: str
    exact: bool
    predicted_gain: int
    predicted_value: int


@dataclass(frozen=True)
class RewardEstimate:
    """Calculated result for a loyalty reward before or after apply."""

    province_no: int
    governor: Officer
    governor_name: str
    target_officer: Officer
    target_officer_name: str
    reward_type: str
    cost_field: str
    cost_amount: int
    current_loyalty: int
    projected_loyalty: int
    success: bool
    reward_turns_used: int
    reward_turns_remaining: int


PROVINCE_NAMES = {
    "幽州": "Youzhou",
    "幷州": "Bingzhou",
    "冀州": "Jizhou",
    "青州": "Qingzhou",
    "兗州": "Yanzhou",
    "司州": "Sizhou",
    "雍州": "Yongzhou",
    "涼州": "Liangzhou",
    "徐州": "Xuzhou",
    "予州": "Yuzhou",
    "荊州": "Jingzhou",
    "揚州": "Yangzhou",
    "益州": "Yizhou",
    "交州": "Jiaozhou",
}

_reward_usage_by_month: dict[tuple[int, int, int], int] = {}


def get_active_province_no() -> int:
    """Return the active province sequence number."""
    return Province.GetActiveNo()


def get_active_province() -> Province:
    """Return the active province."""
    return Province.FromSequence(get_active_province_no())


def get_active_ruler_no() -> int:
    """Return the active ruler number."""
    return Ruler.GetActiveNo()


def get_active_ruler() -> Ruler:
    """Return the active ruler."""
    return Ruler.FromNo(get_active_ruler_no())


def get_province(province_no: int) -> Province:
    """Return a province by sequence number."""
    return Province.FromSequence(province_no)


def get_ruler_provinces(ruler_no: int | None = None) -> list[Province]:
    """Return provinces controlled by a ruler."""
    target_ruler_no = get_active_ruler_no() if ruler_no is None else ruler_no
    return Province.GetListByRulerNo(target_ruler_no)


def get_province_officers(province_no: int) -> list[Officer]:
    """Return officers currently assigned to a province."""
    return get_province(province_no).GetOfficerList()


def get_actionable_officers(province_no: int) -> list[Officer]:
    """Return officers who can still act this month."""
    return [officer for officer in get_province_officers(province_no) if officer.CanAction()]


def get_rewardable_officers(province_no: int) -> list[Officer]:
    """Return officers who can receive a reward."""
    province = get_province(province_no)
    return [
        officer
        for officer in province.GetOfficerList()
        if officer.Offset != province.GovernorOffset
    ]


def can_view_province_freely(province_no: int) -> bool:
    """Return True if viewing this province does not consume an action."""
    return get_province(province_no).RulerNo == get_active_ruler_no()


def consume_officer_action(officer: Officer) -> None:
    """Mark an officer as having used their action this month."""
    officer.SetActionStatus()


def consume_officer_actions(officers: list[Officer]) -> None:
    """Mark multiple officers as having used their action this month."""
    for officer in officers:
        consume_officer_action(officer)


def consume_action_for_foreign_view(province_no: int, officer: Officer | None) -> bool:
    """Consume an action for foreign inspection when required."""
    if can_view_province_freely(province_no):
        return True
    if officer is None:
        return False
    consume_officer_action(officer)
    return True


def get_reward_turn_limit() -> int:
    """Return how many rewards a leader may issue in a month."""
    settings = get_settings()
    return max(1, settings.reward_turns_per_month)


def get_horse_reward_gold_value() -> int:
    """Return the effective gold value used for horse rewards."""
    settings = get_settings()
    return max(1, settings.horse_reward_gold_value)


def _get_current_month_key() -> tuple[int, int]:
    """Return the current in-game year and month."""
    year = Data.BUF[0x44] + Data.BUF[0x45] * 256
    month = Data.BUF[0x46]
    return (year, month)


def _get_reward_usage_key(governor: Officer) -> tuple[int, int, int]:
    """Return the key used to track monthly reward usage."""
    year, month = _get_current_month_key()
    return (year, month, governor.Offset)


def get_reward_turns_used(province_no: int) -> int:
    """Return how many rewards the province governor has used this month."""
    governor = Officer.FromOffset(get_province(province_no).GovernorOffset)
    return _reward_usage_by_month.get(_get_reward_usage_key(governor), 0)


def get_reward_turns_remaining(province_no: int) -> int:
    """Return how many rewards the governor may still issue this month."""
    limit = get_reward_turn_limit()
    return max(0, limit - get_reward_turns_used(province_no))


def can_governor_reward(province_no: int) -> bool:
    """Return True if the province governor can still issue rewards this month."""
    province = get_province(province_no)
    governor = Officer.FromOffset(province.GovernorOffset)
    return governor.CanAction() and get_reward_turns_remaining(province_no) > 0


def _register_reward_use(province_no: int) -> tuple[int, int]:
    """Record one reward use and consume the governor action when quota is exhausted."""
    province = get_province(province_no)
    governor = Officer.FromOffset(province.GovernorOffset)
    usage_key = _get_reward_usage_key(governor)
    used = _reward_usage_by_month.get(usage_key, 0) + 1
    limit = get_reward_turn_limit()
    _reward_usage_by_month[usage_key] = used
    remaining = max(0, limit - used)
    if remaining == 0:
        consume_officer_action(governor)
    return used, remaining


def get_reward_governor(province_no: int) -> Officer:
    """Return the governor who issues province rewards."""
    return Officer.FromOffset(get_province(province_no).GovernorOffset)


def get_province_name(province: Province) -> str:
    """Return an English-friendly province name."""
    name = province.Name
    for chinese, english in PROVINCE_NAMES.items():
        if chinese in name:
            return name.replace(chinese, english)
    return name


def build_officer_rows(province_no: int) -> list[OfficerRow]:
    """Build UI-ready officer rows for a province."""
    rows: list[OfficerRow] = []
    for officer in get_province_officers(province_no):
        rows.append(
            OfficerRow(
                officer=officer,
                name=get_officer_display_name(officer),
                loyalty=officer.Loyalty,
                intelligence=officer.Int,
                war=officer.War,
                charm=officer.Chm,
                service=getattr(officer, "Age", 0),
                soldiers=officer.Soldiers,
                arms=officer.Arms,
                training=officer.TrainingLevel,
            )
        )
    return rows


def build_territory_rows(ruler_no: int | None = None) -> list[TerritoryRow]:
    """Build UI-ready territory rows for a ruler's provinces."""
    rows: list[TerritoryRow] = []
    for province in sorted(get_ruler_provinces(ruler_no), key=lambda item: item.No):
        governor = Officer.FromOffset(province.GovernorOffset)
        rows.append(
            TerritoryRow(
                province_no=province.No,
                province_name=get_province_name(province),
                governor_name=get_officer_display_name(governor),
                gold=province.Gold,
                rice=province.Food,
                soldiers=province.Soldiers,
                general_count=len(province.GetOfficerList()),
                loyalty=province.Loyalty,
            )
        )
    return rows


def calculate_gold_reward(province_no: int, target_officer: Officer, gold: int) -> RewardEstimate:
    """Calculate projected loyalty change for a gold reward."""
    province = get_province(province_no)
    governor = get_reward_governor(province_no)
    current_loyalty = target_officer.Loyalty
    projected_loyalty = _calculate_reward_loyalty(governor.Chm, current_loyalty, gold)
    used = get_reward_turns_used(province_no)
    remaining = max(0, get_reward_turn_limit() - (used + 1))
    return RewardEstimate(
        province_no=province_no,
        governor=governor,
        governor_name=get_officer_display_name(governor),
        target_officer=target_officer,
        target_officer_name=get_officer_display_name(target_officer),
        reward_type="Gold",
        cost_field="Gold",
        cost_amount=gold,
        current_loyalty=current_loyalty,
        projected_loyalty=projected_loyalty,
        success=projected_loyalty > current_loyalty,
        reward_turns_used=used + 1,
        reward_turns_remaining=remaining,
    )


def calculate_horse_reward(province_no: int, target_officer: Officer) -> RewardEstimate:
    """Calculate projected loyalty change for a horse reward."""
    estimate = calculate_gold_reward(province_no, target_officer, get_horse_reward_gold_value())
    return RewardEstimate(
        province_no=estimate.province_no,
        governor=estimate.governor,
        governor_name=estimate.governor_name,
        target_officer=estimate.target_officer,
        target_officer_name=estimate.target_officer_name,
        reward_type="Horse",
        cost_field="Horse",
        cost_amount=1,
        current_loyalty=estimate.current_loyalty,
        projected_loyalty=estimate.projected_loyalty,
        success=estimate.success,
        reward_turns_used=estimate.reward_turns_used,
        reward_turns_remaining=estimate.reward_turns_remaining,
    )


def apply_gold_reward(
    province_no: int,
    target_officer: Officer,
    gold: int,
    estimate: RewardEstimate | None = None,
) -> RewardEstimate:
    """Apply a gold reward and consume one reward use."""
    if estimate is None:
        estimate = calculate_gold_reward(province_no, target_officer, gold)
    province = get_province(province_no)
    province.Gold -= gold
    province.Flush()
    target_officer.Loyalty = estimate.projected_loyalty
    target_officer.Flush()
    used, remaining = _register_reward_use(province_no)
    return RewardEstimate(
        province_no=estimate.province_no,
        governor=estimate.governor,
        governor_name=estimate.governor_name,
        target_officer=estimate.target_officer,
        target_officer_name=estimate.target_officer_name,
        reward_type=estimate.reward_type,
        cost_field=estimate.cost_field,
        cost_amount=estimate.cost_amount,
        current_loyalty=estimate.current_loyalty,
        projected_loyalty=estimate.projected_loyalty,
        success=estimate.success,
        reward_turns_used=used,
        reward_turns_remaining=remaining,
    )


def apply_horse_reward(
    province_no: int,
    target_officer: Officer,
    estimate: RewardEstimate | None = None,
) -> RewardEstimate:
    """Apply a horse reward and consume one reward use."""
    if estimate is None:
        estimate = calculate_horse_reward(province_no, target_officer)
    province = get_province(province_no)
    province.Horses -= 1
    province.Flush()
    target_officer.Loyalty = estimate.projected_loyalty
    target_officer.Flush()
    used, remaining = _register_reward_use(province_no)
    return RewardEstimate(
        province_no=estimate.province_no,
        governor=estimate.governor,
        governor_name=estimate.governor_name,
        target_officer=estimate.target_officer,
        target_officer_name=estimate.target_officer_name,
        reward_type=estimate.reward_type,
        cost_field=estimate.cost_field,
        cost_amount=estimate.cost_amount,
        current_loyalty=estimate.current_loyalty,
        projected_loyalty=estimate.projected_loyalty,
        success=estimate.success,
        reward_turns_used=used,
        reward_turns_remaining=remaining,
    )


def _calculate_reward_loyalty(
    governor_charm: int, current_loyalty: int, reward_gold_value: int
) -> int:
    """Return projected loyalty using the legacy reward formula."""
    result = int((governor_charm * reward_gold_value) / 0x190)
    if result < 1:
        return current_loyalty

    projected_loyalty = current_loyalty + result + random.randint(0, 1)
    return min(100, projected_loyalty)


def get_advisor_in_province(province_no: int) -> Officer | None:
    """Return the current ruler's advisor if they are present in the province."""
    advisor = Officer.GetAdvisor()
    if advisor is None:
        return None

    for officer in get_province_officers(province_no):
        if officer.Offset == advisor.Offset:
            return advisor

    return None


def get_actionable_officer_count(province_no: int) -> int:
    """Return how many officers in the province can still act this month."""
    return len(get_actionable_officers(province_no))


def get_internal_affairs_max_spend(province_no: int, resource_amount: int) -> int:
    """Return the SNES-style spend cap for internal-affairs commands."""
    return min(resource_amount, get_actionable_officer_count(province_no) * 100)


def get_internal_affairs_max_spend_for_selection(
    resource_amount: int, selected_officer_count: int
) -> int:
    """Return the SNES-style spend cap for a specific multi-officer selection."""
    return min(resource_amount, max(0, selected_officer_count) * 100)


def _resolve_internal_officers(officers: list[Officer] | None, officer: Officer) -> list[Officer]:
    """Return the selected officers or fall back to the lead officer."""
    if officers:
        return officers
    return [officer]


def _average_officer_stat(officers: list[Officer], attr_name: str) -> int:
    """Return the floor average of an officer stat across the selection."""
    if not officers:
        return 0
    return sum(getattr(officer, attr_name, 0) for officer in officers) // len(officers)


def calculate_improve_land(
    province_no: int, officer: Officer, spend: int, officers: list[Officer] | None = None
) -> InternalActionEstimate:
    """Calculate projected land improvement using the legacy formula."""
    province = get_province(province_no)
    acting_officers = _resolve_internal_officers(officers, officer)
    current_value = province.Land
    gain = 0
    if current_value < 100:
        half_value = int(current_value / 2)
        avg_charm = _average_officer_stat(acting_officers, "Chm")
        avg_intelligence = _average_officer_stat(acting_officers, "Int")
        v1 = int(
            math.sqrt(
                int((100 - half_value) * spend / 100) * (int(avg_charm / 2) + avg_intelligence)
            )
        )
        difficulty_factor = int((Data.GAME_DIFFCULTY + 1) / 2)
        gain = int(math.sqrt(int(v1 / difficulty_factor))) - difficulty_factor
        if gain < 0:
            gain = 0

    projected_value = min(100, current_value + gain)
    return InternalActionEstimate(
        province_no=province_no,
        officer=officer,
        officer_name=get_officer_display_name(officer),
        officer_count=len(acting_officers),
        action_name="Improve Land",
        cost_field="Gold",
        cost_amount=spend,
        current_value=current_value,
        projected_gain=gain,
        projected_value=projected_value,
    )


def calculate_flood_control(
    province_no: int, officer: Officer, spend: int, officers: list[Officer] | None = None
) -> InternalActionEstimate:
    """Calculate projected flood-control improvement using the legacy formula."""
    province = get_province(province_no)
    acting_officers = _resolve_internal_officers(officers, officer)
    current_value = province.Flood
    gain = 0
    if current_value < 100:
        half_value = int(current_value / 2)
        avg_charm = _average_officer_stat(acting_officers, "Chm")
        avg_intelligence = _average_officer_stat(acting_officers, "Int")
        v1 = int(
            math.sqrt(
                int((100 - half_value) * spend / 100) * (int(avg_charm / 2) + avg_intelligence)
            )
        )
        difficulty_factor = int((Data.GAME_DIFFCULTY + 1) / 2)
        gain = int(math.sqrt(int(v1 / difficulty_factor))) - difficulty_factor
        if gain < 0:
            gain = 0

    projected_value = min(100, current_value + gain)
    return InternalActionEstimate(
        province_no=province_no,
        officer=officer,
        officer_name=get_officer_display_name(officer),
        officer_count=len(acting_officers),
        action_name="Flood Control",
        cost_field="Gold",
        cost_amount=spend,
        current_value=current_value,
        projected_gain=gain,
        projected_value=projected_value,
    )


def calculate_give_food(
    province_no: int, officer: Officer, spend: int, officers: list[Officer] | None = None
) -> InternalActionEstimate:
    """Calculate projected loyalty gain using the legacy give-food formula."""
    province = get_province(province_no)
    acting_officers = _resolve_internal_officers(officers, officer)
    current_value = province.Loyalty
    gain = 0
    if current_value < 100:
        ruler = Ruler.FromNo(province.RulerNo).RulerSelf
        avg_charm = _average_officer_stat(acting_officers, "Chm")
        v1 = int(math.sqrt(spend)) * int((ruler.Chm + avg_charm) / 2)
        v2 = (6 + Data.GAME_DIFFCULTY) * int(math.sqrt(province.Population / 100))
        gain = int(v1 / v2) if v2 > 0 else 0

    projected_value = min(100, current_value + gain)
    return InternalActionEstimate(
        province_no=province_no,
        officer=officer,
        officer_name=get_officer_display_name(officer),
        officer_count=len(acting_officers),
        action_name="Give Food",
        cost_field="Food",
        cost_amount=spend,
        current_value=current_value,
        projected_gain=gain,
        projected_value=projected_value,
    )


def get_advisor_opinion(estimate: InternalActionEstimate) -> AdvisorOpinion | None:
    """Return an advisor prediction for the estimate when an advisor is present."""
    advisor = get_advisor_in_province(estimate.province_no)
    if advisor is None:
        return None

    exact = advisor.Int >= 95
    if exact:
        predicted_gain = estimate.projected_gain
    elif advisor.Int >= 80:
        predicted_gain = max(
            0, estimate.projected_gain + _advisor_prediction_offset(advisor.Int, 1)
        )
    elif advisor.Int >= 60:
        predicted_gain = max(
            0, estimate.projected_gain + _advisor_prediction_offset(advisor.Int, 2)
        )
    else:
        predicted_gain = max(
            0, estimate.projected_gain + _advisor_prediction_offset(advisor.Int, 4)
        )

    predicted_value = min(100, estimate.current_value + predicted_gain)
    return AdvisorOpinion(
        advisor=advisor,
        advisor_name=get_officer_display_name(advisor),
        exact=exact,
        predicted_gain=predicted_gain,
        predicted_value=predicted_value,
    )


def apply_improve_land(province_no: int, officer: Officer, spend: int) -> InternalActionEstimate:
    """Apply land improvement, preserving legacy waste behavior."""
    estimate = calculate_improve_land(province_no, officer, spend)
    province = get_province(province_no)
    province.Gold -= spend
    province.Land = estimate.projected_value
    province.Flush()
    consume_officer_action(officer)
    return estimate


def apply_improve_land_with_officers(
    province_no: int, officer: Officer, spend: int, selected_officers: list[Officer]
) -> InternalActionEstimate:
    """Apply land improvement and consume all selected officers."""
    estimate = calculate_improve_land(province_no, officer, spend, selected_officers)
    province = get_province(province_no)
    province.Gold -= spend
    province.Land = estimate.projected_value
    province.Flush()
    consume_officer_actions(selected_officers)
    return estimate


def apply_flood_control(province_no: int, officer: Officer, spend: int) -> InternalActionEstimate:
    """Apply flood-control improvement, preserving legacy waste behavior."""
    estimate = calculate_flood_control(province_no, officer, spend)
    province = get_province(province_no)
    province.Gold -= spend
    province.Flood = estimate.projected_value
    province.Flush()
    consume_officer_action(officer)
    return estimate


def apply_flood_control_with_officers(
    province_no: int, officer: Officer, spend: int, selected_officers: list[Officer]
) -> InternalActionEstimate:
    """Apply flood control and consume all selected officers."""
    estimate = calculate_flood_control(province_no, officer, spend, selected_officers)
    province = get_province(province_no)
    province.Gold -= spend
    province.Flood = estimate.projected_value
    province.Flush()
    consume_officer_actions(selected_officers)
    return estimate


def apply_give_food(province_no: int, officer: Officer, spend: int) -> InternalActionEstimate:
    """Apply give-food loyalty improvement, preserving legacy waste behavior."""
    estimate = calculate_give_food(province_no, officer, spend)
    province = get_province(province_no)
    province.Food -= spend
    province.Loyalty = estimate.projected_value
    province.Flush()
    consume_officer_action(officer)
    return estimate


def apply_give_food_with_officers(
    province_no: int, officer: Officer, spend: int, selected_officers: list[Officer]
) -> InternalActionEstimate:
    """Apply give food and consume all selected officers."""
    estimate = calculate_give_food(province_no, officer, spend, selected_officers)
    province = get_province(province_no)
    province.Food -= spend
    province.Loyalty = estimate.projected_value
    province.Flush()
    consume_officer_actions(selected_officers)
    return estimate


def _advisor_prediction_offset(advisor_int: int, spread: int) -> int:
    """Return a deterministic advisor prediction error based on advisor Int."""
    seed = advisor_int * 7 + Data.GAME_DIFFCULTY * 13
    return (seed % (spread * 2 + 1)) - spread
