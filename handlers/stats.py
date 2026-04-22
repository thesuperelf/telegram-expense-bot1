import logging
from datetime import date, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.common import navigation_keyboard
from keyboards.stats import stats_period_keyboard
from services.stats_service import get_stats
from services.user_service import get_or_create_user
from states.stats_states import StatsRangeState
from utils.formatting import format_amount, format_dt
from utils.validators import parse_date

router = Router()
logger = logging.getLogger(__name__)


async def send_stats(
    message: Message,
    session: AsyncSession,
    user_id: int,
    date_from: date,
    date_to: date,
) -> None:
    stats = await get_stats(session, user_id, date_from, date_to)

    lines = [
        f"📊 Статистика за период {date_from:%d.%m.%Y} — {date_to:%d.%m.%Y}",
        f"\nОбщая сумма: {format_amount(stats.total)}",
        f"Операций: {stats.operations_count}",
        "\nПо категориям:",
    ]

    if stats.categories:
        for item in stats.categories:
            lines.append(f"• {item.category}: {format_amount(item.total)} ({item.percent:.1f}%)")
    else:
        lines.append("• Нет данных")

    lines.append("\nТоп-5 последних расходов в периоде:")
    if stats.top_expenses:
        for expense in stats.top_expenses:
            lines.append(
                f"• {format_dt(expense.created_at)} | {format_amount(expense.amount)} | {expense.category.name}"
            )
    else:
        lines.append("• Нет расходов")

    await message.answer("\n".join(lines), reply_markup=stats_period_keyboard())


@router.message(F.text == "Статистика")
async def stats_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Выберите период для статистики:", reply_markup=stats_period_keyboard())


@router.message(F.text.in_({"Сегодня", "7 дней", "30 дней", "Этот месяц"}))
async def handle_quick_stats(message: Message, session: AsyncSession) -> None:
    today = date.today()
    if message.text == "Сегодня":
        start = end = today
    elif message.text == "7 дней":
        start, end = today - timedelta(days=6), today
    elif message.text == "30 дней":
        start, end = today - timedelta(days=29), today
    else:
        start = today.replace(day=1)
        end = today

    user = await get_or_create_user(session, message.from_user.id)
    await session.commit()
    await send_stats(message, session, user.id, start, end)
    logger.info("Stats shown: user_id=%s start=%s end=%s", message.from_user.id, start, end)


@router.message(F.text == "Произвольный диапазон")
async def custom_stats_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(StatsRangeState.waiting_start_date)
    await message.answer(
        "Введите дату начала в формате YYYY-MM-DD:",
        reply_markup=navigation_keyboard(),
    )


@router.message(StatsRangeState.waiting_start_date)
async def custom_stats_start_date(message: Message, state: FSMContext) -> None:
    start = parse_date(message.text or "")
    if start is None:
        await message.answer("Неверный формат. Пример: 2026-04-01", reply_markup=navigation_keyboard())
        return

    await state.update_data(start_date=start.isoformat())
    await state.set_state(StatsRangeState.waiting_end_date)
    await message.answer(
        "Введите дату конца в формате YYYY-MM-DD:",
        reply_markup=navigation_keyboard(),
    )


@router.message(StatsRangeState.waiting_end_date)
async def custom_stats_end_date(message: Message, state: FSMContext, session: AsyncSession) -> None:
    end = parse_date(message.text or "")
    data = await state.get_data()
    start = parse_date(data.get("start_date", ""))

    if start is None or end is None:
        await state.clear()
        await message.answer("Ошибка дат. Начните заново из раздела «Статистика».", reply_markup=stats_period_keyboard())
        return
    if end < start:
        await message.answer("Дата конца не может быть раньше даты начала.", reply_markup=navigation_keyboard())
        return

    user = await get_or_create_user(session, message.from_user.id)
    await session.commit()
    await send_stats(message, session, user.id, start, end)
    await state.clear()
    logger.info("Custom stats shown: user_id=%s start=%s end=%s", message.from_user.id, start, end)
