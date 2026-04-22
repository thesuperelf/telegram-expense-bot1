import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.categories import categories_menu_keyboard
from keyboards.common import navigation_keyboard
from services.category_service import (
    CategoryAlreadyExistsError,
    CategoryInUseError,
    CategoryNotFoundError,
    SystemCategoryDeleteError,
    create_user_category,
    delete_user_category,
    list_categories,
)
from services.user_service import get_or_create_user
from states.category_states import CategoryState
from utils.validators import normalize_category_name

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "Категории")
async def categories_menu(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Раздел категорий:", reply_markup=categories_menu_keyboard())


@router.message(F.text == "Список категорий")
async def list_all_categories(message: Message, session: AsyncSession) -> None:
    user = await get_or_create_user(session, message.from_user.id)
    categories = await list_categories(session, user.id)
    await session.commit()

    system_names = [category.name for category in categories if category.is_system]
    user_names = [category.name for category in categories if not category.is_system]

    lines = ["📚 Категории:", "\nСистемные:"]
    lines.extend([f"• {name}" for name in system_names])
    lines.append("\nПользовательские:")
    if user_names:
        lines.extend([f"• {name}" for name in user_names])
    else:
        lines.append("• Нет")

    await message.answer("\n".join(lines), reply_markup=categories_menu_keyboard())


@router.message(F.text == "Добавить категорию")
async def add_category_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CategoryState.waiting_new_category_name)
    await message.answer(
        "Введите название новой категории:",
        reply_markup=navigation_keyboard(),
    )


@router.message(CategoryState.waiting_new_category_name)
async def add_category_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = normalize_category_name(message.text or "")
    if len(name) < 2:
        await message.answer("Название слишком короткое. Минимум 2 символа.", reply_markup=navigation_keyboard())
        return
    if len(name) > 100:
        await message.answer("Название слишком длинное. Максимум 100 символов.", reply_markup=navigation_keyboard())
        return

    user = await get_or_create_user(session, message.from_user.id)
    try:
        category = await create_user_category(session, user.id, name)
    except CategoryAlreadyExistsError as exc:
        await message.answer(
            f"Категория «{exc.args[0]}» уже существует.",
            reply_markup=navigation_keyboard(),
        )
        return

    await session.commit()
    await state.clear()
    logger.info("Category created: user_id=%s name=%s", message.from_user.id, category.name)
    await message.answer(
        f"Категория «{category.name}» добавлена.",
        reply_markup=categories_menu_keyboard(),
    )


@router.message(F.text == "Удалить категорию")
async def delete_category_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(CategoryState.waiting_delete_category_name)
    await message.answer(
        "Введите название пользовательской категории для удаления:",
        reply_markup=navigation_keyboard(),
    )


@router.message(CategoryState.waiting_delete_category_name)
async def delete_category_finish(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = normalize_category_name(message.text or "")
    user = await get_or_create_user(session, message.from_user.id)

    try:
        category = await delete_user_category(session, user.id, name)
    except SystemCategoryDeleteError:
        await message.answer("Системные категории удалять нельзя.", reply_markup=navigation_keyboard())
        return
    except CategoryNotFoundError:
        await message.answer("Категория не найдена.", reply_markup=navigation_keyboard())
        return
    except CategoryInUseError as exc:
        await message.answer(
            f"Категория «{exc.args[0]}» уже используется в расходах и не может быть удалена.",
            reply_markup=navigation_keyboard(),
        )
        return

    await session.commit()
    await state.clear()
    logger.info("Category deleted: user_id=%s name=%s", message.from_user.id, category.name)
    await message.answer(
        f"Категория «{category.name}» удалена.",
        reply_markup=categories_menu_keyboard(),
    )
