import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from keyboards.main_menu import get_main_menu

router = Router()
logger = logging.getLogger(__name__)


@router.message(Command("start"))
async def cmd_start(message: Message) -> None:
    logger.info("Start command received: user_id=%s", message.from_user.id)
    text = (
        "Привет! Я бот для учета личных расходов.\n"
        "Выберите действие в меню ниже."
    )
    await message.answer(text, reply_markup=get_main_menu())


@router.message(Command("help"))
@router.message(lambda message: (message.text or "").strip() == "Помощь")
async def cmd_help(message: Message) -> None:
    logger.info("Help requested: user_id=%s", message.from_user.id)
    help_text = (
        "Доступные действия:\n"
        "• Добавить расход — пошаговое добавление траты\n"
        "• Статистика — анализ расходов за период\n"
        "• Сравнить периоды — сравнение с предыдущим аналогичным периодом\n"
        "• Категории — управление пользовательскими категориями\n"
        "• Последние расходы — 10 последних записей\n"
        "• Удалить расход — удаление записи по ID\n\n"
        "Во всех сценариях с несколькими шагами доступны кнопки «Назад» и «Отмена»."
    )
    await message.answer(help_text, reply_markup=get_main_menu())
