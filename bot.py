import asyncio
import logging

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import ErrorEvent, Message

from config import load_config
from database.init_db import init_db
from database.session import init_engine
from handlers import categories, common, compare, delete_expense, expenses, start, stats
from keyboards.main_menu import get_main_menu
from middlewares.db import DbSessionMiddleware

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


async def on_error(event: ErrorEvent) -> None:
    logger.exception("Ошибка при обработке события: %s", event.exception)

    message = getattr(getattr(event, "update", None), "message", None)
    if isinstance(message, Message):
        await message.answer(
            "Произошла ошибка. Попробуйте еще раз чуть позже.",
            reply_markup=get_main_menu(),
        )


async def main() -> None:
    setup_logging()
    config = load_config()

    engine, session_maker = init_engine(config.database_url)
    await init_db(engine, session_maker)

    bot = Bot(token=config.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    root_router = Router()
    root_router.message.middleware(DbSessionMiddleware(session_maker))
    root_router.include_router(common.router)
    root_router.include_router(start.router)
    root_router.include_router(expenses.router)
    root_router.include_router(stats.router)
    root_router.include_router(compare.router)
    root_router.include_router(categories.router)
    root_router.include_router(delete_expense.router)

    dp.include_router(root_router)
    dp.errors.register(on_error)

    logger.info("Бот запускается")
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    finally:
        logger.info("Бот останавливается")
        await bot.session.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
