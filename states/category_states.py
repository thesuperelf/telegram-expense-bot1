from aiogram.fsm.state import State, StatesGroup


class CategoryState(StatesGroup):
    waiting_new_category_name = State()
    waiting_delete_category_name = State()
