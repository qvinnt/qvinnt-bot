from __future__ import annotations

import asyncio
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
    await message.answer("✌️")

    await asyncio.sleep(1)

    text = """Привет! Я бот Квинта ✌️

Тут ты можешь влиять на то, какие каверы выйдут дальше 😉

🎵 <b>Предложи трек на кавер</b>
<blockquote>Жми <b>Предложить трек</b> или /suggest</blockquote>

🏆 <b>Голосуй за уже предложенные треки</b>
<blockquote>Жми <b>Топ треков</b> или /top</blockquote>"""

    await message.answer(
        text=text,
        reply_markup=MAIN_KEYBOARD,
    )

    deep_link = message.text[7:] if message.text else None
