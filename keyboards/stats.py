from aiogram.types import ReplyKeyboardMarkup

from keyboards.common import BACK_BUTTON_TEXT, make_reply_keyboard


def stats_period_keyboard() -> ReplyKeyboardMarkup:
    return make_reply_keyboard(
        [
            ["Сегодня", "7 дней"],
            ["30 дней", "Этот месяц"],
            ["Произвольный диапазон"],
            [BACK_BUTTON_TEXT],
        ]
    )
