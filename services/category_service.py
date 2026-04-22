from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Category, Expense
from utils.validators import make_category_key, normalize_category_name


class CategoryAlreadyExistsError(Exception):
    pass


class CategoryNotFoundError(Exception):
    pass


class SystemCategoryDeleteError(Exception):
    pass


class CategoryInUseError(Exception):
    pass


def build_user_scope(user_id: int) -> str:
    return f"user:{user_id}"


async def list_categories(session: AsyncSession, user_id: int) -> list[Category]:
    result = await session.scalars(
        select(Category)
        .where(or_(Category.scope_key == "system", Category.user_id == user_id))
        .order_by(Category.is_system.desc(), Category.name.asc())
    )
    return list(result.all())


async def create_user_category(session: AsyncSession, user_id: int, name: str) -> Category:
    normalized_name = make_category_key(name)
    existing = await session.scalar(
        select(Category).where(
            Category.normalized_name == normalized_name,
            or_(Category.scope_key == "system", Category.user_id == user_id),
        )
    )
    if existing:
        raise CategoryAlreadyExistsError(existing.name)

    category = Category(
        user_id=user_id,
        scope_key=build_user_scope(user_id),
        name=normalize_category_name(name),
        normalized_name=normalized_name,
        is_system=False,
    )
    session.add(category)
    await session.flush()
    return category


async def delete_user_category(session: AsyncSession, user_id: int, name: str) -> Category:
    normalized_name = make_category_key(name)
    category = await session.scalar(
        select(Category).where(
            Category.user_id == user_id,
            Category.normalized_name == normalized_name,
        )
    )
    if category is None:
        system_category = await session.scalar(
            select(Category).where(
                Category.scope_key == "system",
                Category.normalized_name == normalized_name,
            )
        )
        if system_category is not None:
            raise SystemCategoryDeleteError(system_category.name)
        raise CategoryNotFoundError(name)

    used_expense = await session.scalar(
        select(Expense.id).where(Expense.category_id == category.id).limit(1)
    )
    if used_expense is not None:
        raise CategoryInUseError(category.name)

    await session.delete(category)
    await session.flush()
    return category
