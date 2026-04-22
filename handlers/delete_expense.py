import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.common import confirm_delete_keyboard, navigation_keyboard
from keyboards.main_menu import get_main_menu
from services.expense_service import delete_expense, get_expense_by_id, get_last_expenses
from services.user_service import get_or_create_user
from states.delete_states import DeleteExpenseState
from utils.formatting import format_amount, format_dt

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "Удалить расход")
async def delete_start(message: Message, state: FSMContext, session: AsyncSession) -> None:
    await state.clear()
    user = await get_or_create_user(session, message.from_user.id)
    expenses = await get_last_expenses(session, user.id, limit=10)
    await session.commit()

    if not expenses:
        await message.answer("У вас нет расходов для удаления.", reply_markup=get_main_menu())
        return

    lines = ["Выберите ID расхода для удаления. Последние 10 записей:"]
    for expense in expenses:
        lines.append(
            f"ID: {expense.id} | {format_dt(expense.created_at)} | "
            f"{format_amount(expense.amount)} | {expense.category.name}"
        )

    prompt_text = "\n".join(lines)
    await state.update_data(delete_prompt=prompt_text)
    await state.set_state(DeleteExpenseState.waiting_expense_id)
    await message.answer(prompt_text, reply_markup=navigation_keyboard())


@router.message(DeleteExpenseState.waiting_expense_id)
async def delete_choose_id(message: Message, state: FSMContext, session: AsyncSession) -> None:
    if not (message.text or "").isdigit():
        await message.answer("Введите числовой ID расхода.", reply_markup=navigation_keyboard())
        return

    expense_id = int(message.text)
    user = await get_or_create_user(session, message.from_user.id)
    expense = await get_expense_by_id(session, user.id, expense_id)
    await session.commit()

    if expense is None:
        await message.answer("Расход с таким ID не найден.", reply_markup=navigation_keyboard())
        return

    await state.update_data(expense_id=expense_id)
    await state.set_state(DeleteExpenseState.waiting_confirmation)
    await message.answer(
        "Подтвердите удаление:\n"
        f"ID: {expense.id}\n"
        f"Дата: {format_dt(expense.created_at)}\n"
        f"Сумма: {format_amount(expense.amount)}\n"
        f"Категория: {expense.category.name}",
        reply_markup=confirm_delete_keyboard(),
    )


@router.message(DeleteExpenseState.waiting_confirmation, F.text == "Подтвердить удаление")
async def delete_confirm(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    expense_id = data.get("expense_id")
    if not expense_id:
        await state.clear()
        await message.answer("Ошибка удаления. Повторите попытку.", reply_markup=get_main_menu())
        return

    user = await get_or_create_user(session, message.from_user.id)
    expense = await get_expense_by_id(session, user.id, int(expense_id))
    if expense is None:
        await state.clear()
        await message.answer("Расход не найден.", reply_markup=get_main_menu())
        return

    await delete_expense(session, expense)
    await session.commit()
    await state.clear()
    logger.info("Expense deleted: user_id=%s expense_id=%s", message.from_user.id, expense_id)
    await message.answer("✅ Расход удален.", reply_markup=get_main_menu())
