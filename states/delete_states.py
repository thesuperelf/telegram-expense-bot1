from aiogram.fsm.state import State, StatesGroup


class DeleteExpenseState(StatesGroup):
    waiting_expense_id = State()
    waiting_confirmation = State()
