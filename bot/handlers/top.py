from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import Command
from aiogram_dialog import StartMode

from bot.states.top import TopSG

if TYPE_CHECKING:
    from aiogram import types
    from aiogram_dialog import DialogManager

router = Router(name=__name__)


@router.message(Command("top"))
async def handle_top_command(
    message: types.Message,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.start(
        TopSG.waiting_for_action,
        mode=StartMode.RESET_STACK,
    )
