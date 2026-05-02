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
    """Calculated result for a reward before or after apply."""

    province_no: int
    governor: Officer
    governor_name: str
    target_officer: Officer
    target_officer_name: str
    reward_type: str
    cost_field: str
    cost_amount: int
    stat_name: str
    current_value: int
    projected_value: int
    success: bool
    reward_turns_used: int
    reward_turns_remaining: int
    detail_text: str = ""
    failure_reason: str = ""


@dataclass(frozen=True)
class TrainingEstimate:
    """Calculated result for province training before or after apply."""

    province_no: int
    officer: Officer
    officer_name: str
    officer_count: int
    current_training: int
    projected_training: int
    projected_gain: int
    total_soldier_hundreds: int


@dataclass(frozen=True)
class ProvinceAdvanceResult:
    """Result of advancing the active province within the ruler's province chain."""

    advanced: bool
    current_province_no: int
    next_province_no: int | None
    reached_end_of_cycle: bool


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


def set_active_province_no(province_no: int) -> Province:
    """Set the active province pointer to the given province."""
    province = Province.FromSequence(province_no)
    Data.SetWordToOffset(Data.BUF, province.Offset, Data.CURRENT_PROVINCE_OFFSET)
    return province


def advance_to_next_owned_province() -> ProvinceAdvanceResult:
    """Advance to the next owned province in the active ruler's linked province chain."""
    current_province_no = get_active_province_no()
    provinces = get_ruler_provinces()
    province_numbers = [province.No for province in provinces]

    try:
        current_index = province_numbers.index(current_province_no)
    except ValueError:
        if provinces:
            next_province = set_active_province_no(provinces[0].No)
            return ProvinceAdvanceResult(
                advanced=True,
                current_province_no=current_province_no,
                next_province_no=next_province.No,
                reached_end_of_cycle=False,
            )

        return ProvinceAdvanceResult(
            advanced=False,
            current_province_no=current_province_no,
            next_province_no=None,
            reached_end_of_cycle=True,
        )

    if current_index + 1 >= len(provinces):
        return ProvinceAdvanceResult(
            advanced=False,
            current_province_no=current_province_no,
            next_province_no=None,
            reached_end_of_cycle=True,
        )

    next_province = set_active_province_no(provinces[current_index + 1].No)
    return ProvinceAdvanceResult(
        advanced=True,
        current_province_no=current_province_no,
        next_province_no=next_province.No,
        reached_end_of_cycle=False,
    )


def get_province_officers(province_no: int) -> list[Officer]:
    """Return officers currently assigned to a province."""
    return get_province(province_no).GetOfficerList()


def get_actionable_officers(province_no: int) -> list[Officer]:
    """Return officers who can still act this month."""
    return [officer for officer in get_province_officers(province_no) if officer.CanAction()]


def get_rewardable_officers(province_no: int) -> list[Officer]:
    """Return officers who can receive a reward.

    Legacy Command11 behavior only hides the governor when the governor is the
    current ruler. A non-ruler governor remains a valid reward target.
    """
    province = get_province(province_no)
    current_ruler_officer_offset = Data.GetWordFromOffset(
        Data.BUF, Data.CURRENT_RULER_OFFICER_OFFSET
    )
    officer_list = province.GetOfficerList()
    if province.GovernorOffset == current_ruler_officer_offset:
        return [officer for officer in officer_list if officer.Offset != province.GovernorOffset]
    return officer_list


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


def get_book_reward_max_increase() -> int:
    """Return the maximum random increase for book rewards."""
    settings = get_settings()
    return max(1, settings.book_reward_max_increase)


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


def can_use_book_reward(province_no: int) -> bool:
    """Return True if book reward may be used in the province."""
    return get_advisor_in_province(province_no) is not None


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


def can_train_province(province_no: int) -> bool:
    """Return True if province training can still improve at least one officer."""
    return any(officer.TrainingLevel < 100 for officer in get_province_officers(province_no))


def get_training_candidates(province_no: int) -> list[Officer]:
    """Return officers who can lead training this month."""
    return get_actionable_officers(province_no)


def calculate_training(
    province_no: int, officer: Officer, officers: list[Officer] | None = None
) -> TrainingEstimate:
    """Calculate projected province training using the legacy formula."""
    province_officers = get_province_officers(province_no)
    acting_officers = _resolve_internal_officers(officers, officer)
    current_training = min(
        (
            min(officer_item.TrainingLevel for officer_item in province_officers)
            if province_officers
            else 0
        ),
        100,
    )
    total_soldier_hundreds = sum(
        int(officer_item.Soldiers / 100) for officer_item in province_officers
    )
    soldier_factor = int(math.sqrt(total_soldier_hundreds + 1))
    avg_war = _average_officer_stat(acting_officers, "War")
    projected_gain = int(avg_war * 2 / soldier_factor) if soldier_factor > 0 else 0
    highest_current_training = max(
        (officer_item.TrainingLevel for officer_item in province_officers), default=0
    )
    projected_training = min(100, highest_current_training + projected_gain)
    return TrainingEstimate(
        province_no=province_no,
        officer=officer,
        officer_name=get_officer_display_name(officer),
        officer_count=len(acting_officers),
        current_training=highest_current_training,
        projected_training=projected_training,
        projected_gain=projected_gain,
        total_soldier_hundreds=total_soldier_hundreds,
    )


def apply_training(
    province_no: int, officer: Officer, selected_officers: list[Officer] | None = None
) -> TrainingEstimate:
    """Apply province training to all officers and consume the trainer's action."""
    acting_officers = _resolve_internal_officers(selected_officers, officer)
    estimate = calculate_training(province_no, officer, acting_officers)
    for province_officer in get_province_officers(province_no):
        province_officer.TrainingLevel = min(
            100, province_officer.TrainingLevel + estimate.projected_gain
        )
        province_officer.Flush()
    consume_officer_actions(acting_officers)
    return estimate


def calculate_gold_reward(province_no: int, target_officer: Officer, gold: int) -> RewardEstimate:
    """Calculate projected loyalty change for a gold reward."""
    governor = get_reward_governor(province_no)
    current_value = target_officer.Loyalty
    projected_value = _calculate_reward_loyalty(governor.Chm, current_value, gold)
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
        stat_name="Loyalty",
        current_value=current_value,
        projected_value=projected_value,
        success=projected_value > current_value,
        reward_turns_used=used + 1,
        reward_turns_remaining=remaining,
        detail_text=f"Governor charm {governor.Chm} determines the loyalty gain.",
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
        stat_name=estimate.stat_name,
        current_value=estimate.current_value,
        projected_value=estimate.projected_value,
        success=estimate.success,
        reward_turns_used=estimate.reward_turns_used,
        reward_turns_remaining=estimate.reward_turns_remaining,
        detail_text=(
            f"Horse rewards use an effective gold value of {get_horse_reward_gold_value():,}."
        ),
        failure_reason=estimate.failure_reason,
    )


def calculate_book_reward(province_no: int, target_officer: Officer) -> RewardEstimate:
    """Calculate projected intelligence change for a book reward."""
    governor = get_reward_governor(province_no)
    advisor = get_advisor_in_province(province_no)
    current_value = target_officer.Int
    used = get_reward_turns_used(province_no)
    remaining = max(0, get_reward_turn_limit() - (used + 1))

    if advisor is None:
        return RewardEstimate(
            province_no=province_no,
            governor=governor,
            governor_name=get_officer_display_name(governor),
            target_officer=target_officer,
            target_officer_name=get_officer_display_name(target_officer),
            reward_type="Book",
            cost_field="Reward Use",
            cost_amount=1,
            stat_name="Intelligence",
            current_value=current_value,
            projected_value=current_value,
            success=False,
            reward_turns_used=used + 1,
            reward_turns_remaining=remaining,
            failure_reason="No advisor is present in this province.",
        )

    max_allowed = min(100, advisor.Int - 1)
    if current_value + 1 > max_allowed:
        return RewardEstimate(
            province_no=province_no,
            governor=governor,
            governor_name=get_officer_display_name(governor),
            target_officer=target_officer,
            target_officer_name=get_officer_display_name(target_officer),
            reward_type="Book",
            cost_field="Reward Use",
            cost_amount=1,
            stat_name="Intelligence",
            current_value=current_value,
            projected_value=current_value,
            success=False,
            reward_turns_used=used + 1,
            reward_turns_remaining=remaining,
            detail_text=f"Advisor {get_officer_display_name(advisor)} has Int {advisor.Int}.",
            failure_reason="This officer cannot gain even 1 Intelligence without reaching the advisor cap.",
        )

    rolled_increase = random.randint(1, get_book_reward_max_increase())
    projected_value = min(current_value + rolled_increase, max_allowed)
    return RewardEstimate(
        province_no=province_no,
        governor=governor,
        governor_name=get_officer_display_name(governor),
        target_officer=target_officer,
        target_officer_name=get_officer_display_name(target_officer),
        reward_type="Book",
        cost_field="Reward Use",
        cost_amount=1,
        stat_name="Intelligence",
        current_value=current_value,
        projected_value=projected_value,
        success=projected_value > current_value,
        reward_turns_used=used + 1,
        reward_turns_remaining=remaining,
        detail_text=(
            f"Advisor {get_officer_display_name(advisor)} has Int {advisor.Int}. "
            f"Book gain rolls 1-{get_book_reward_max_increase()}, capped below the advisor's Int."
        ),
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
    target_officer.Loyalty = estimate.projected_value
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
        stat_name=estimate.stat_name,
        current_value=estimate.current_value,
        projected_value=estimate.projected_value,
        success=estimate.success,
        reward_turns_used=used,
        reward_turns_remaining=remaining,
        detail_text=estimate.detail_text,
        failure_reason=estimate.failure_reason,
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
    target_officer.Loyalty = estimate.projected_value
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
        stat_name=estimate.stat_name,
        current_value=estimate.current_value,
        projected_value=estimate.projected_value,
        success=estimate.success,
        reward_turns_used=used,
        reward_turns_remaining=remaining,
        detail_text=estimate.detail_text,
        failure_reason=estimate.failure_reason,
    )


def apply_book_reward(
    province_no: int,
    target_officer: Officer,
    estimate: RewardEstimate | None = None,
) -> RewardEstimate:
    """Apply a book reward and consume one reward use."""
    if estimate is None:
        estimate = calculate_book_reward(province_no, target_officer)
    target_officer.Int = estimate.projected_value
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
        stat_name=estimate.stat_name,
        current_value=estimate.current_value,
        projected_value=estimate.projected_value,
        success=estimate.success,
        reward_turns_used=used,
        reward_turns_remaining=remaining,
        detail_text=estimate.detail_text,
        failure_reason=estimate.failure_reason,
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
