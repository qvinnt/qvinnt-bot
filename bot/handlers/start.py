from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram_dialog import StartMode

from bot.states.example import ExampleSG

if TYPE_CHECKING:
    from aiogram import types
    from aiogram_dialog import DialogManager

router = Router(name=__name__)


@router.message(CommandStart())
async def handle_start_command(
    message: types.Message,
    dialog_manager: DialogManager,
) -> None:
    deep_link = message.text[7:] if message.text else None

    await message.answer(f"<a href='t.me/qvinnt_bot?start=123'>Голосовать</a>\n{deep_link}")
    # await message.answer("👋")

    # await dialog_manager.start(
    #     ExampleSG.example,
    #     mode=StartMode.RESET_STACK,
    # )
