from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import Command
from aiogram_dialog import StartMode

from bot.states.admin.track import AdminTrackSG

if TYPE_CHECKING:
    from aiogram import types
    from aiogram_dialog import DialogManager

router = Router(name=__name__)


@router.message(Command("track"))
async def handle_suggest_command(
    message: types.Message,
    dialog_manager: DialogManager,
) -> None:
    if message.text != "/track":
        track_query = message.text.split(" ", 1)[1]

    await dialog_manager.start(
        AdminTrackSG.waiting_for_action,
        mode=StartMode.RESET_STACK,
        data={
            "track_query": track_query,
        },
    )
