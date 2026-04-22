import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.categories import categories_choice_keyboard
from keyboards.common import SKIP_BUTTON_TEXT, navigation_keyboard, skip_keyboard
from keyboards.main_menu import get_main_menu
from services.category_service import list_categories
from services.expense_service import ExpenseCategoryNotFoundError, add_expense, get_last_expenses
from services.user_service import get_or_create_user
from states.expense_states import AddExpenseState
from utils.formatting import format_amount, format_dt
from utils.validators import make_category_key, parse_amount

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "Добавить расход")
async def add_expense_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AddExpenseState.waiting_amount)
    logger.info("Expense flow started: user_id=%s", message.from_user.id)
    await message.answer(
        "Введите сумму расхода. Например: 450 или 450.75",
        reply_markup=navigation_keyboard(),
    )


@router.message(AddExpenseState.waiting_amount)
async def add_expense_amount(message: Message, state: FSMContext, session: AsyncSession) -> None:
    try:
        amount = parse_amount(message.text or "")
    except ValueError as exc:
        await message.answer(str(exc), reply_markup=navigation_keyboard())
        return

    user = await get_or_create_user(session, message.from_user.id)
    categories = await list_categories(session, user.id)
    await session.commit()

    await state.update_data(amount=str(amount), categories=[category.name for category in categories])
    await state.set_state(AddExpenseState.waiting_category)
    await message.answer(
        "Выберите категорию расхода:",
        reply_markup=categories_choice_keyboard([category.name for category in categories]),
    )


@router.message(AddExpenseState.waiting_category)
async def add_expense_category(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    categories: list[str] = data.get("categories", [])
    category_map = {make_category_key(name): name for name in categories}
    category = category_map.get(make_category_key(message.text or ""))

    if category is None:
        await message.answer(
            "Не удалось определить категорию. Выберите ее кнопкой или введите точное название.",
            reply_markup=categories_choice_keyboard(categories),
        )
        return

    await state.update_data(category=category)
    await state.set_state(AddExpenseState.waiting_comment)
    await message.answer(
        "Введите комментарий или нажмите «Пропустить».",
        reply_markup=skip_keyboard(),
    )


@router.message(AddExpenseState.waiting_comment)
async def add_expense_comment(message: Message, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    amount_value = data.get("amount")
    category = data.get("category")

    if not amount_value or not category:
        await state.clear()
        await message.answer("Сценарий сбился. Начните добавление заново.", reply_markup=get_main_menu())
        return

    try:
        amount = parse_amount(amount_value)
    except ValueError:
        await state.clear()
        await message.answer("Сумма больше недоступна. Начните добавление заново.", reply_markup=get_main_menu())
        return

    comment_text = (message.text or "").strip()
    comment = None if comment_text == SKIP_BUTTON_TEXT else comment_text or None

    user = await get_or_create_user(session, message.from_user.id)
    try:
        expense = await add_expense(session, user.id, amount, category, comment)
    except ExpenseCategoryNotFoundError:
        await state.clear()
        await message.answer(
            "Категория больше недоступна. Начните добавление расхода заново.",
            reply_markup=get_main_menu(),
        )
        return

    await session.commit()
    await session.refresh(expense)
    await state.clear()

    logger.info(
        "Expense saved: user_id=%s expense_id=%s amount=%s category=%s",
        message.from_user.id,
        expense.id,
        expense.amount,
        category,
    )
    await message.answer(
        "✅ Расход сохранен:\n"
        f"Сумма: {format_amount(expense.amount)}\n"
        f"Категория: {category}\n"
        f"Комментарий: {comment or '—'}",
        reply_markup=get_main_menu(),
    )


@router.message(F.text == "Последние расходы")
async def show_last_expenses(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(session, message.from_user.id)
    expenses = await get_last_expenses(session, user.id, limit=10)
    await session.commit()

    if not expenses:
        await message.answer("У вас пока нет расходов.", reply_markup=get_main_menu())
        return

    lines = ["🧾 Последние 10 расходов:"]
    for expense in expenses:
        comment = f"\nКомментарий: {expense.comment}" if expense.comment else ""
        lines.append(
            f"\nID: {expense.id}\n"
            f"Дата: {format_dt(expense.created_at)}\n"
            f"Сумма: {format_amount(expense.amount)}\n"
            f"Категория: {expense.category.name}{comment}"
        )

    await message.answer("\n".join(lines), reply_markup=get_main_menu())
