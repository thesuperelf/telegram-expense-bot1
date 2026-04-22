from dataclasses import dataclass
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Category, Expense


@dataclass(slots=True)
class CategoryStat:
    category: str
    total: Decimal
    percent: float


@dataclass(slots=True)
class StatsResult:
    total: Decimal
    operations_count: int
    categories: list[CategoryStat]
    top_expenses: list[Expense]


async def get_stats(session: AsyncSession, user_id: int, date_from: date, date_to: date) -> StatsResult:
    dt_from = datetime.combine(date_from, time.min)
    dt_to = datetime.combine(date_to, time.max)

    total = await session.scalar(
        select(func.coalesce(func.sum(Expense.amount), 0)).where(
            Expense.user_id == user_id,
            Expense.created_at >= dt_from,
            Expense.created_at <= dt_to,
        )
    )
    count = await session.scalar(
        select(func.count(Expense.id)).where(
            Expense.user_id == user_id,
            Expense.created_at >= dt_from,
            Expense.created_at <= dt_to,
        )
    )
    grouped = await session.execute(
        select(Category.name, func.sum(Expense.amount).label("total"))
        .join(Category, Category.id == Expense.category_id)
        .where(
            Expense.user_id == user_id,
            Expense.created_at >= dt_from,
            Expense.created_at <= dt_to,
        )
        .group_by(Category.name)
        .order_by(func.sum(Expense.amount).desc())
    )

    top = await session.scalars(
        select(Expense)
        .options(joinedload(Expense.category))
        .where(
            Expense.user_id == user_id,
            Expense.created_at >= dt_from,
            Expense.created_at <= dt_to,
        )
        .order_by(Expense.created_at.desc(), Expense.id.desc())
        .limit(5)
    )

    total_decimal = Decimal(str(total or 0)).quantize(Decimal("0.01"))
    category_stats: list[CategoryStat] = []
    for row in grouped.all():
        cat_total = Decimal(str(row.total)).quantize(Decimal("0.01"))
        percent = float((cat_total / total_decimal * 100) if total_decimal > 0 else 0)
        category_stats.append(CategoryStat(category=row.name, total=cat_total, percent=percent))

    return StatsResult(
        total=total_decimal,
        operations_count=int(count or 0),
        categories=category_stats,
        top_expenses=list(top.all()),
    )
