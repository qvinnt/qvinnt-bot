from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import F, Router
from aiogram.filters import Command
from aiogram_dialog import StartMode

from bot.keyboards.main import TOP_BUTTON
from bot.states.top import TopSG

if TYPE_CHECKING:
    from aiogram import types
    from aiogram_dialog import DialogManager

router = Router(name=__name__)


@router.message(F.text.lower() == TOP_BUTTON.text.lower())
@router.message(Command("top"))
async def handle_top_command(
    message: types.Message,
    dialog_manager: DialogManager,
) -> None:
    await dialog_manager.start(
        TopSG.waiting_for_action,
        mode=StartMode.RESET_STACK,
    )
