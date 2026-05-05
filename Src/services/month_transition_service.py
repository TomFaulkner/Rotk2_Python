"""Month-boundary processing hooks for campaign progression."""

from __future__ import annotations

from dataclasses import dataclass, field
import random

from Data import Data
from Helper import Helper
from Officer import Officer
from Province import Province
from Ruler import Ruler
from . import officer_state_service


@dataclass(frozen=True)
class MonthTransitionSummary:
    """Structured result for month-boundary processing."""

    year: int
    month: int
    messages: list[str] = field(default_factory=list)


def get_current_year() -> int:
    """Return the current in-game year."""
    return Data.BUF[0x44] + Data.BUF[0x45] * 256


def get_current_month() -> int:
    """Return the current zero-based in-game month."""
    return Data.BUF[0x46]


def reset_monthly_officer_actions() -> None:
    """Clear the action-used bit for all officer records."""
    for index in range(Data.MaxNumberOfGenerals):
        offset = Data.OFFICER_START + index * Data.OFFICER_SIZE
        Data.BUF[offset + 2] &= 0xFE


def apply_monthly_loyalty_deductions() -> list[str]:
    """Apply approximate monthly officer loyalty drift based on trust and compatibility."""
    changes: list[str] = []
    for ruler in Ruler.GetList():
        if ruler is None or ruler.RulerSelf is None:
            continue

        trust_full_avoid = False
        if ruler.TrustRating >= 75:
            trust_full_avoid = True
        elif ruler.TrustRating >= 60:
            trust_full_avoid = random.random() < 0.65

        for province in Province.GetListByRulerNo(ruler.No):
            for officer in province.GetOfficerList():
                if officer.Offset == ruler.RulerSelf.Offset:
                    continue
                if officer.Loyalty <= 0:
                    continue

                if officer.xueyuan > 0 and officer.xueyuan == getattr(
                    ruler.RulerSelf, "xueyuan", 0
                ):
                    continue
                if officer_state_service.has_item_reward_from_current_ruler(officer):
                    continue
                if trust_full_avoid:
                    continue

                years = officer_state_service.get_years_of_service(officer)
                compat_diff = abs(ruler.RulerSelf.Compatibility - officer.Compatibility)
                avoidance_score = 100 + years - compat_diff
                trust_bonus = max(0, (ruler.TrustRating - 50) // 2)
                avoidance_score = max(10, min(180, avoidance_score + trust_bonus))
                roll = random.randint(0, 99)
                if roll < avoidance_score:
                    continue

                drop_amount = random.choice([3, 4, 5, 5, 5, 6, 7])
                if compat_diff > 40:
                    drop_amount += 2
                elif compat_diff > 25:
                    drop_amount += 1
                if ruler.TrustRating < 40:
                    drop_amount += 2

                old_loyalty = officer.Loyalty
                officer.Loyalty = max(0, officer.Loyalty - drop_amount)
                officer.Flush()
                changes.append(
                    f"{officer.GetName()} loyalty {old_loyalty}->{officer.Loyalty} under {ruler.RulerSelf.GetName()}."
                )

    for change in changes:
        print(f"[month-transition] {change}")

    return changes


def process_monthly_random_events() -> list[str]:
    """Placeholder hook for future omens, arrivals, and random events."""
    return []


def process_month_transition() -> MonthTransitionSummary:
    """Advance the game month and run the month-boundary processing pipeline."""
    month = get_current_month() + 1
    year = get_current_year()
    if month >= 12:
        month = 0
        year += 1

    Data.BUF[0x44] = year % 256
    Data.BUF[0x45] = year >> 8
    Data.BUF[0x46] = month

    officer_state_service.synchronize_officer_ruler_state()
    if month == 0:
        officer_state_service.increment_years_of_service()

    messages: list[str] = []
    messages.extend(apply_monthly_loyalty_deductions())
    messages.extend(process_monthly_random_events())

    reset_monthly_officer_actions()
    Helper.GetRulersOrder()

    return MonthTransitionSummary(year=year, month=month, messages=messages)
