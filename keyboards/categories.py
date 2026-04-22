from aiogram.types import ReplyKeyboardMarkup

from keyboards.common import BACK_BUTTON_TEXT, CANCEL_BUTTON_TEXT, make_reply_keyboard


def categories_menu_keyboard() -> ReplyKeyboardMarkup:
    return make_reply_keyboard(
        [
            ["Список категорий"],
            ["Добавить категорию", "Удалить категорию"],
            [BACK_BUTTON_TEXT],
        ]
    )


def categories_choice_keyboard(names: list[str]) -> ReplyKeyboardMarkup:
    rows: list[list[str]] = []
    current_row: list[str] = []

    for name in names:
        current_row.append(name)
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []

    if current_row:
        rows.append(current_row)

    rows.append([BACK_BUTTON_TEXT, CANCEL_BUTTON_TEXT])
    return make_reply_keyboard(rows)
