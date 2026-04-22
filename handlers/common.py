import logging
from dataclasses import dataclass
from typing import Any, Callable

from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import Message, ReplyKeyboardMarkup

from keyboards.categories import categories_choice_keyboard, categories_menu_keyboard
from keyboards.common import BACK_BUTTON_TEXT, CANCEL_BUTTON_TEXT, navigation_keyboard
from keyboards.compare import compare_period_keyboard
from keyboards.main_menu import get_main_menu
from keyboards.stats import stats_period_keyboard
from states.category_states import CategoryState
from states.compare_states import CompareRangeState
from states.delete_states import DeleteExpenseState
from states.expense_states import AddExpenseState
from states.stats_states import StatsRangeState

router = Router()
logger = logging.getLogger(__name__)


def text_equals(value: str | None, expected: str) -> bool:
    return (value or "").strip().casefold() == expected.casefold()


@dataclass(slots=True, frozen=True)
class BackRoute:
    target_state: State | None
    text_builder: Callable[[dict[str, Any]], str]
    markup_builder: Callable[[dict[str, Any]], ReplyKeyboardMarkup]
    drop_keys: tuple[str, ...] = ()


BACK_ROUTES: dict[str, BackRoute] = {
    AddExpenseState.waiting_amount.state: BackRoute(
        target_state=None,
        text_builder=lambda _: "Возвращаемся в главное меню.",
        markup_builder=lambda _: get_main_menu(),
    ),
    AddExpenseState.waiting_category.state: BackRoute(
        target_state=AddExpenseState.waiting_amount,
        text_builder=lambda _: "Введите сумму расхода. Например: 450 или 450.75",
        markup_builder=lambda _: navigation_keyboard(),
        drop_keys=("amount", "category"),
    ),
    AddExpenseState.waiting_comment.state: BackRoute(
        target_state=AddExpenseState.waiting_category,
        text_builder=lambda _: "Выберите категорию расхода:",
        markup_builder=lambda data: categories_choice_keyboard(data.get("categories", [])),
        drop_keys=("category",),
    ),
    CategoryState.waiting_new_category_name.state: BackRoute(
        target_state=None,
        text_builder=lambda _: "Возвращаемся в раздел категорий.",
        markup_builder=lambda _: categories_menu_keyboard(),
    ),
    CategoryState.waiting_delete_category_name.state: BackRoute(
        target_state=None,
        text_builder=lambda _: "Возвращаемся в раздел категорий.",
        markup_builder=lambda _: categories_menu_keyboard(),
    ),
    StatsRangeState.waiting_start_date.state: BackRoute(
        target_state=None,
        text_builder=lambda _: "Выберите период для статистики:",
        markup_builder=lambda _: stats_period_keyboard(),
    ),
    StatsRangeState.waiting_end_date.state: BackRoute(
        target_state=StatsRangeState.waiting_start_date,
        text_builder=lambda _: "Введите дату начала в формате YYYY-MM-DD:",
        markup_builder=lambda _: navigation_keyboard(),
        drop_keys=("start_date",),
    ),
    CompareRangeState.waiting_start_date.state: BackRoute(
        target_state=None,
        text_builder=lambda _: "Выберите вариант сравнения:",
        markup_builder=lambda _: compare_period_keyboard(),
    ),
    CompareRangeState.waiting_end_date.state: BackRoute(
        target_state=CompareRangeState.waiting_start_date,
        text_builder=lambda _: "Введите дату начала текущего периода в формате YYYY-MM-DD:",
        markup_builder=lambda _: navigation_keyboard(),
        drop_keys=("start_date",),
    ),
    DeleteExpenseState.waiting_expense_id.state: BackRoute(
        target_state=None,
        text_builder=lambda _: "Удаление отменено. Возвращаемся в главное меню.",
        markup_builder=lambda _: get_main_menu(),
    ),
    DeleteExpenseState.waiting_confirmation.state: BackRoute(
        target_state=DeleteExpenseState.waiting_expense_id,
        text_builder=lambda data: data.get("delete_prompt", "Введите ID расхода для удаления:"),
        markup_builder=lambda _: navigation_keyboard(),
        drop_keys=("expense_id",),
    ),
}


@router.message(StateFilter("*"), lambda message: text_equals(message.text, CANCEL_BUTTON_TEXT))
async def cancel_fsm_action(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    await state.clear()
    logger.info("FSM cancelled: user_id=%s state=%s", message.from_user.id, current_state)
    await message.answer("Текущее действие отменено.", reply_markup=get_main_menu())


@router.message(StateFilter("*"), lambda message: text_equals(message.text, BACK_BUTTON_TEXT))
async def go_back_in_fsm(message: Message, state: FSMContext) -> None:
    current_state = await state.get_state()
    route = BACK_ROUTES.get(current_state or "")
    data = await state.get_data()

    if route is None:
        await state.clear()
        await message.answer("Возвращаемся в главное меню.", reply_markup=get_main_menu())
        return

    for key in route.drop_keys:
        data.pop(key, None)

    if route.target_state is None:
        await state.clear()
    else:
        await state.set_data(data)
        await state.set_state(route.target_state)

    logger.info(
        "FSM back: user_id=%s from_state=%s to_state=%s",
        message.from_user.id,
        current_state,
        route.target_state,
    )
    await message.answer(route.text_builder(data), reply_markup=route.markup_builder(data))


@router.message(lambda message: text_equals(message.text, BACK_BUTTON_TEXT))
async def back_to_main_menu(message: Message, state: FSMContext) -> None:
    if await state.get_state():
        return
    await message.answer("Главное меню:", reply_markup=get_main_menu())


@router.message(lambda message: text_equals(message.text, CANCEL_BUTTON_TEXT))
async def cancel_without_active_state(message: Message, state: FSMContext) -> None:
    if await state.get_state():
        return
    await message.answer("Сейчас нет активного действия.", reply_markup=get_main_menu())
