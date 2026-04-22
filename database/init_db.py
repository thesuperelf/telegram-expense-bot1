from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker

from database.models import Base, Category
from utils.validators import make_category_key

SYSTEM_CATEGORIES = [
    "Еда",
    "Транспорт",
    "Дом",
    "Здоровье",
    "Развлечения",
    "Подписки",
    "Одежда",
    "Подарки",
    "Другое",
]


async def init_db(engine: AsyncEngine, session_maker: async_sessionmaker) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_maker() as session:
        existing = await session.scalars(
            select(Category.normalized_name).where(Category.scope_key == "system")
        )
        existing_names = set(existing.all())

        for name in SYSTEM_CATEGORIES:
            normalized_name = make_category_key(name)
            if normalized_name in existing_names:
                continue

            session.add(
                Category(
                    user_id=None,
                    scope_key="system",
                    name=name,
                    normalized_name=normalized_name,
                    is_system=True,
                )
            )

        await session.commit()
