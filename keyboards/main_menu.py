from aiogram.types import ReplyKeyboardMarkup

from keyboards.common import make_reply_keyboard


def get_main_menu() -> ReplyKeyboardMarkup:
    return make_reply_keyboard(
        [
            ["Добавить расход", "Статистика"],
            ["Сравнить периоды", "Категории"],
            ["Последние расходы", "Удалить расход"],
            ["Помощь"],
        ]
    )
