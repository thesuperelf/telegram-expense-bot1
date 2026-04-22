from aiogram.types import ReplyKeyboardMarkup

from keyboards.common import BACK_BUTTON_TEXT, make_reply_keyboard


def compare_period_keyboard() -> ReplyKeyboardMarkup:
    return make_reply_keyboard(
        [
            ["Сегодня vs вчера"],
            ["7 дней vs предыдущие 7 дней"],
            ["30 дней vs предыдущие 30 дней"],
            ["Этот месяц vs прошлый месяц"],
            ["Произвольный диапазон vs предыдущий"],
            [BACK_BUTTON_TEXT],
        ]
    )
