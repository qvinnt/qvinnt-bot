from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.filters import Command
from aiogram_dialog import StartMode

from bot.keyboards.main import SUGGEST_BUTTON
from bot.states.suggest import SuggestSG

if TYPE_CHECKING:
    from aiogram import types
    from aiogram_dialog import DialogManager

router = Router(name=__name__)


@router.message(F.text.lower() == SUGGEST_BUTTON.text.lower())
@router.message(Command("suggest"))
async def handle_suggest_command(
    message: types.Message,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.start(
        SuggestSG.waiting_for_track,
        mode=StartMode.RESET_STACK,
        data={
            "first": True,
        },
    )
