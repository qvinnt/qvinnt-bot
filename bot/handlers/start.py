from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram_dialog import StartMode

from bot.keyboards.main import MAIN_KEYBOARD
from bot.services import track as track_service
from bot.states.vote import VoteSG

if TYPE_CHECKING:
    from aiogram import types
    from aiogram_dialog import DialogManager
    from posthog import Posthog
    from sqlalchemy.ext.asyncio import AsyncSession

router = Router(name=__name__)


@router.message(CommandStart())
async def handle_start_command(
    message: types.Message,
    dialog_manager: DialogManager,
    session: AsyncSession,
    posthog: Posthog,
) -> None:
    posthog.capture(event="command used", properties={"command": "start"})

    await message.answer("✌️")

    await asyncio.sleep(1)

    text = """Привет! Я бот Квинта ✌️

Есть идея для кавера? Делись👇

📩 <b>Предложи трек на кавер</b>
<blockquote>Жми [Предложить трек] или /suggest</blockquote>

🏆 <b>Голосуй за уже предложенные треки</b>
<blockquote>Жми [Топ треков] или /top</blockquote>"""

    await message.answer(
        text=text,
        reply_markup=MAIN_KEYBOARD,
    )

    deep_link = message.text[7:] if message.text else None

    if deep_link and deep_link.startswith("vote_") and deep_link[5:].isdigit():
        track_id = int(deep_link[5:])

        track = await track_service.get_track_by_id(session, track_id)

        if track and not track.is_released and not track.is_denied:
            await asyncio.sleep(1)

            await dialog_manager.start(
                VoteSG.waiting_for_action,
                mode=StartMode.RESET_STACK,
                data={
                    "track_id": track_id,
                },
            )
