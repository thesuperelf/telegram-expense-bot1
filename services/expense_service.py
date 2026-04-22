from decimal import Decimal

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from database.models import Category, Expense
from utils.validators import make_category_key


class ExpenseCategoryNotFoundError(Exception):
    pass


async def add_expense(
    session: AsyncSession,
    user_id: int,
    amount: Decimal,
    category_name: str,
    comment: str | None,
) -> Expense:
    normalized_name = make_category_key(category_name)
    category = await session.scalar(
        select(Category).where(
            Category.normalized_name == normalized_name,
            or_(Category.scope_key == "system", Category.user_id == user_id),
        )
    )
    if category is None:
        raise ExpenseCategoryNotFoundError(category_name)

    expense = Expense(
        user_id=user_id,
        category_id=category.id,
        amount=amount,
        comment=comment,
    )
    session.add(expense)
    await session.flush()
    return expense


async def get_last_expenses(session: AsyncSession, user_id: int, limit: int = 10) -> list[Expense]:
    result = await session.scalars(
        select(Expense)
        .options(joinedload(Expense.category))
        .where(Expense.user_id == user_id)
        .order_by(Expense.created_at.desc(), Expense.id.desc())
        .limit(limit)
    )
    return list(result.all())


async def get_expense_by_id(session: AsyncSession, user_id: int, expense_id: int) -> Expense | None:
    return await session.scalar(
        select(Expense)
        .options(joinedload(Expense.category))
        .where(Expense.id == expense_id, Expense.user_id == user_id)
    )


async def delete_expense(session: AsyncSession, expense: Expense) -> None:
    await session.delete(expense)
    await session.flush()
