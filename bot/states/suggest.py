from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class SuggestSG(StatesGroup):
    waiting_for_track = State()
    waiting_for_existing_not_released_track_action = State()
    waiting_for_existing_released_track_action = State()
    waiting_for_existing_denied_track_action = State()
    waiting_for_new_track_selection = State()
