from aiogram.fsm.state import State, StatesGroup


class StatsRangeState(StatesGroup):
    waiting_start_date = State()
    waiting_end_date = State()
