from aiogram.fsm.state import State, StatesGroup


class AddExpenseState(StatesGroup):
    waiting_amount = State()
    waiting_category = State()
    waiting_comment = State()
