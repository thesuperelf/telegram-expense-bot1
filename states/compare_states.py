from aiogram.fsm.state import State, StatesGroup


class CompareRangeState(StatesGroup):
    waiting_start_date = State()
    waiting_end_date = State()
