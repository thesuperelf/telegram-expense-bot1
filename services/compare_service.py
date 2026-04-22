from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from services.stats_service import get_stats


@dataclass(slots=True)
class CompareResult:
    current_total: Decimal
    previous_total: Decimal
    diff_abs: Decimal
    diff_percent: float | None
    current_categories: dict[str, Decimal]
    previous_categories: dict[str, Decimal]


async def compare_periods(
    session: AsyncSession,
    user_id: int,
    current_start: date,
    current_end: date,
    previous_start: date,
    previous_end: date,
) -> CompareResult:
    current_stats = await get_stats(session, user_id, current_start, current_end)
    previous_stats = await get_stats(session, user_id, previous_start, previous_end)

    diff_abs = (current_stats.total - previous_stats.total).quantize(Decimal("0.01"))
    if previous_stats.total == 0:
        diff_percent = None
    else:
        diff_percent = float((diff_abs / previous_stats.total) * 100)

    return CompareResult(
        current_total=current_stats.total,
        previous_total=previous_stats.total,
        diff_abs=diff_abs,
        diff_percent=diff_percent,
        current_categories={item.category: item.total for item in current_stats.categories},
        previous_categories={item.category: item.total for item in previous_stats.categories},
    )


def previous_equal_period(start: date, end: date) -> tuple[date, date]:
    delta_days = (end - start).days + 1
    prev_end = start - timedelta(days=1)
    prev_start = prev_end - timedelta(days=delta_days - 1)
    return prev_start, prev_end
