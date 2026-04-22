from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

BACK_BUTTON_TEXT = "Назад"
CANCEL_BUTTON_TEXT = "Отмена"
SKIP_BUTTON_TEXT = "Пропустить"


def make_reply_keyboard(rows: list[list[str]]) -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text=text) for text in row] for row in rows]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def navigation_keyboard(
    *,
    include_back: bool = True,
    include_cancel: bool = True,
    extra_rows: list[list[str]] | None = None,
) -> ReplyKeyboardMarkup:
    rows = list(extra_rows or [])
    navigation_row: list[str] = []

    if include_back:
        navigation_row.append(BACK_BUTTON_TEXT)
    if include_cancel:
        navigation_row.append(CANCEL_BUTTON_TEXT)
    if navigation_row:
        rows.append(navigation_row)

    return make_reply_keyboard(rows)


def skip_keyboard() -> ReplyKeyboardMarkup:
    return navigation_keyboard(extra_rows=[[SKIP_BUTTON_TEXT]])


def confirm_delete_keyboard() -> ReplyKeyboardMarkup:
    return navigation_keyboard(extra_rows=[["Подтвердить удаление"]])
