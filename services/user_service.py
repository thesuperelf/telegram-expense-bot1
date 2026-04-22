from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User


async def get_or_create_user(session: AsyncSession, telegram_user_id: int) -> User:
    user = await session.scalar(select(User).where(User.telegram_user_id == telegram_user_id))
    if user is not None:
        return user

    user = User(telegram_user_id=telegram_user_id)
    session.add(user)
    await session.flush()
    return user
