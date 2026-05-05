"""Peaceful-only campaign automation for delegated and non-human rulers."""

from __future__ import annotations

from dataclasses import dataclass

from Data import DelegateMode
from Officer import Officer
from Province import Province
from officer_display import get_officer_display_name
from . import province_command_service as province_service


@dataclass(frozen=True)
class ProvinceAutomationResult:
    """Summary of a single province's automated peaceful actions."""

    province_no: int
    summary: str


def run_peaceful_turn_for_ruler(ruler_no: int) -> list[ProvinceAutomationResult]:
    """Run peaceful-only automation across all provinces owned by a ruler."""
    results: list[ProvinceAutomationResult] = []
    for province in province_service.get_ruler_provinces(ruler_no):
        result = run_peaceful_turn_for_province(province.No)
        if result is not None:
            results.append(result)
    return results


def run_peaceful_turn_for_province(province_no: int) -> ProvinceAutomationResult | None:
    """Run a single province's peaceful automation plan."""
    province = Province.FromSequence(province_no)
    actionable_officers = province_service.get_actionable_officers(province_no)
    if not actionable_officers:
        return None

    delegate_mode = Province.GetDelegateStatus(province_no)
    if delegate_mode == DelegateMode.Internal:
        return _run_internal_plan(province, actionable_officers)
    if delegate_mode == DelegateMode.Military:
        return _run_military_plan(province, actionable_officers)
    if delegate_mode == DelegateMode.Person:
        return _run_personnel_plan(province, actionable_officers)
    return _run_balanced_plan(province, actionable_officers)


def _run_balanced_plan(
    province: Province, actionable_officers: list[Officer]
) -> ProvinceAutomationResult | None:
    """Run a safe balanced automation plan for a province."""
    result = _run_internal_plan(province, actionable_officers)
    if result is not None:
        return result
    return _run_personnel_plan(province, province_service.get_actionable_officers(province.No))


def _run_internal_plan(
    province: Province, actionable_officers: list[Officer]
) -> ProvinceAutomationResult | None:
    """Improve land or flood control, falling back to give food."""
    officers = province_service.get_actionable_officers(province.No)
    if not officers:
        return None

    if province.Land < 100 and province.Gold >= 100:
        return _apply_improve_land(province, officers)
    if province.Flood < 100 and province.Gold >= 100:
        return _apply_flood_control(province, officers)
    if province.Loyalty < 95 and province.Food >= 100:
        return _apply_give_food(province, officers)
    return None


def _run_military_plan(
    province: Province, actionable_officers: list[Officer]
) -> ProvinceAutomationResult | None:
    """Run a peaceful military plan via training only."""
    officers = province_service.get_actionable_officers(province.No)
    if not officers:
        return None
    if not province_service.can_train_province(province.No):
        return None

    estimate = province_service.apply_training(province.No, officers[0], officers)
    return ProvinceAutomationResult(
        province_no=province.No,
        summary=(
            f"Province {province.No}: trained troops +{estimate.projected_gain} "
            f"using {estimate.officer_count} officers."
        ),
    )


def _run_personnel_plan(
    province: Province, actionable_officers: list[Officer]
) -> ProvinceAutomationResult | None:
    """Run a peaceful personnel plan through rewards."""
    if not province_service.can_governor_reward(province.No):
        return None

    targets = [
        officer
        for officer in province_service.get_rewardable_officers(province.No)
        if officer.Loyalty < 95
    ]
    if not targets:
        return None

    target = min(targets, key=lambda officer: officer.Loyalty)
    if province.Gold >= 100:
        estimate = province_service.calculate_gold_reward(province.No, target, 100)
        result = province_service.apply_gold_reward(province.No, target, 100, estimate)
        return ProvinceAutomationResult(
            province_no=province.No,
            summary=(
                f"Province {province.No}: rewarded {result.target_officer_name} with gold "
                f"({result.current_value}->{result.projected_value} loyalty)."
            ),
        )
    if province.Horses > 0:
        estimate = province_service.calculate_horse_reward(province.No, target)
        result = province_service.apply_horse_reward(province.No, target, estimate)
        return ProvinceAutomationResult(
            province_no=province.No,
            summary=(
                f"Province {province.No}: rewarded {result.target_officer_name} with a horse "
                f"({result.current_value}->{result.projected_value} loyalty)."
            ),
        )
    return None


def _apply_improve_land(province: Province, officers: list[Officer]) -> ProvinceAutomationResult:
    """Apply safe land development."""
    spend = min(province.Gold, max(100, min(len(officers) * 100, 300)))
    estimate = province_service.apply_improve_land_with_officers(
        province.No, officers[0], spend, officers
    )
    return ProvinceAutomationResult(
        province_no=province.No,
        summary=(
            f"Province {province.No}: developed land +{estimate.projected_gain} "
            f"using {estimate.officer_count} officers."
        ),
    )


def _apply_flood_control(province: Province, officers: list[Officer]) -> ProvinceAutomationResult:
    """Apply safe flood-control improvement."""
    spend = min(province.Gold, max(100, min(len(officers) * 100, 300)))
    estimate = province_service.apply_flood_control_with_officers(
        province.No, officers[0], spend, officers
    )
    return ProvinceAutomationResult(
        province_no=province.No,
        summary=(
            f"Province {province.No}: improved flood control +{estimate.projected_gain} "
            f"using {estimate.officer_count} officers."
        ),
    )


def _apply_give_food(province: Province, officers: list[Officer]) -> ProvinceAutomationResult:
    """Apply safe food distribution for loyalty."""
    spend = min(province.Food, max(100, min(len(officers) * 100, 300)))
    estimate = province_service.apply_give_food_with_officers(
        province.No, officers[0], spend, officers
    )
    ruler_name = get_officer_display_name(Officer.FromOffset(province.GovernorOffset))
    return ProvinceAutomationResult(
        province_no=province.No,
        summary=(
            f"Province {province.No}: {ruler_name} distributed food "
            f"({estimate.current_value}->{estimate.projected_value} loyalty)."
        ),
    )
