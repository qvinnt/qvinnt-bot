from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class SuggestSG(StatesGroup):
    waiting_for_track = State()
    waiting_for_confirmation = State()
