from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import CommandStart

from bot.keyboards.main import MAIN_KEYBOARD

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

    await message.answer(
        "Привет! Я бот для голосования за треки. Выбери действие:",
        reply_markup=MAIN_KEYBOARD,
    )
