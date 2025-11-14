from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class VoteSG(StatesGroup):
    waiting_for_action = State()
