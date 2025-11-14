from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class SuggestSG(StatesGroup):
    waiting_for_track = State()
    waiting_for_existing_not_done_track_action = State()
    waiting_for_existing_done_track_action = State()
    waiting_for_new_track_selection = State()
