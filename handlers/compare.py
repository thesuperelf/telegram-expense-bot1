import logging
from datetime import date, timedelta

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.common import navigation_keyboard
from keyboards.compare import compare_period_keyboard
from services.compare_service import compare_periods, previous_equal_period
from services.user_service import get_or_create_user
from states.compare_states import CompareRangeState
from utils.formatting import format_amount
from utils.validators import parse_date

router = Router()
logger = logging.getLogger(__name__)


def month_bounds(day: date) -> tuple[date, date]:
    start = day.replace(day=1)
    if day.month == 12:
        next_month = day.replace(year=day.year + 1, month=1, day=1)
    else:
        next_month = day.replace(month=day.month + 1, day=1)
    end = next_month - timedelta(days=1)
    return start, end


async def send_compare(
    message: Message,
    session: AsyncSession,
    user_id: int,
    current_start: date,
    current_end: date,
    previous_start: date,
    previous_end: date,
) -> None:
    result = await compare_periods(
        session=session,
        user_id=user_id,
        current_start=current_start,
        current_end=current_end,
        previous_start=previous_start,
        previous_end=previous_end,
    )

    if result.diff_percent is None:
        trend_text = "В предыдущем периоде не было расходов, процент изменения не рассчитывается."
    elif result.diff_percent > 0:
        trend_text = f"Расходы выросли на {result.diff_percent:.1f}%"
    elif result.diff_percent < 0:
        trend_text = f"Расходы снизились на {abs(result.diff_percent):.1f}%"
    else:
        trend_text = "Расходы не изменились."

    lines = [
        f"📈 Сравнение периодов:\n{current_start:%d.%m.%Y}—{current_end:%d.%m.%Y} vs "
        f"{previous_start:%d.%m.%Y}—{previous_end:%d.%m.%Y}",
        f"\nТекущий период: {format_amount(result.current_total)}",
        f"Предыдущий период: {format_amount(result.previous_total)}",
        f"Разница: {format_amount(result.diff_abs)}",
        trend_text,
        "\nПо категориям:",
    ]

    all_categories = sorted(set(result.current_categories) | set(result.previous_categories))
    if not all_categories:
        lines.append("• Нет данных")
    else:
        for category_name in all_categories:
            current_total = result.current_categories.get(category_name, 0)
            previous_total = result.previous_categories.get(category_name, 0)
            diff = current_total - previous_total
            mark = "↗" if diff > 0 else "↘" if diff < 0 else "→"
            lines.append(
                f"• {category_name}: {format_amount(current_total)} vs "
                f"{format_amount(previous_total)} ({mark} {format_amount(diff)})"
            )

    await message.answer("\n".join(lines), reply_markup=compare_period_keyboard())


@router.message(F.text == "Сравнить периоды")
async def compare_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Выберите вариант сравнения:", reply_markup=compare_period_keyboard())


@router.message(
    F.text.in_(
        {
            "Сегодня vs вчера",
            "7 дней vs предыдущие 7 дней",
            "30 дней vs предыдущие 30 дней",
            "Этот месяц vs прошлый месяц",
        }
    )
)
async def compare_quick(message: Message, session: AsyncSession) -> None:
    today = date.today()
    if message.text == "Сегодня vs вчера":
        current_start = current_end = today
        previous_start = previous_end = today - timedelta(days=1)
    elif message.text == "7 дней vs предыдущие 7 дней":
        current_start, current_end = today - timedelta(days=6), today
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=6)
    elif message.text == "30 дней vs предыдущие 30 дней":
        current_start, current_end = today - timedelta(days=29), today
        previous_end = current_start - timedelta(days=1)
        previous_start = previous_end - timedelta(days=29)
    else:
        current_start, current_end = month_bounds(today)
        previous_month_day = current_start - timedelta(days=1)
        previous_start, previous_end = month_bounds(previous_month_day)

    user = await get_or_create_user(session, message.from_user.id)
    await session.commit()
    await send_compare(
        message=message,
        session=session,
        user_id=user.id,
        current_start=current_start,
        current_end=current_end,
        previous_start=previous_start,
        previous_end=previous_end,
    )
    logger.info(
        "Quick compare shown: user_id=%s current=%s..%s previous=%s..%s",
        message.from_user.id,
        current_start,
        current_end,
        previous_start,
        previous_end,
    )


@router.message(F.text == "Произвольный диапазон vs предыдущий")
async def compare_custom_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CompareRangeState.waiting_start_date)
    await message.answer(
        "Введите дату начала текущего периода в формате YYYY-MM-DD:",
        reply_markup=navigation_keyboard(),
    )


@router.message(CompareRangeState.waiting_start_date)
async def compare_custom_start_date(message: Message, state: FSMContext) -> None:
    start = parse_date(message.text or "")
    if start is None:
        await message.answer("Неверный формат даты. Пример: 2026-04-01", reply_markup=navigation_keyboard())
        return

    await state.update_data(start_date=start.isoformat())
    await state.set_state(CompareRangeState.waiting_end_date)
    await message.answer(
        "Введите дату конца текущего периода в формате YYYY-MM-DD:",
        reply_markup=navigation_keyboard(),
    )


@router.message(CompareRangeState.waiting_end_date)
async def compare_custom_end_date(message: Message, state: FSMContext, session: AsyncSession) -> None:
    end = parse_date(message.text or "")
    data = await state.get_data()
    start = parse_date(data.get("start_date", ""))

    if start is None or end is None:
        await state.clear()
        await message.answer("Ошибка дат. Начните заново.", reply_markup=compare_period_keyboard())
        return
    if end < start:
        await message.answer("Дата конца не может быть раньше даты начала.", reply_markup=navigation_keyboard())
        return

    previous_start, previous_end = previous_equal_period(start, end)
    user = await get_or_create_user(session, message.from_user.id)
    await session.commit()
    await send_compare(
        message=message,
        session=session,
        user_id=user.id,
        current_start=start,
        current_end=end,
        previous_start=previous_start,
        previous_end=previous_end,
    )
    await state.clear()
    logger.info(
        "Custom compare shown: user_id=%s current=%s..%s previous=%s..%s",
        message.from_user.id,
        start,
        end,
        previous_start,
        previous_end,
    )
