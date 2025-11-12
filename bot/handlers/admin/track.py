from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import Command
from aiogram_dialog import StartMode

from bot.services import track as track_service
from bot.states.admin.track import AdminTrackSG

if TYPE_CHECKING:
    from aiogram import types
    from aiogram_dialog import DialogManager
    from sqlalchemy.ext.asyncio import AsyncSession

router = Router(name=__name__)


@router.message(Command("track"))
async def handle_suggest_command(
    message: types.Message,
    dialog_manager: DialogManager,
    session: AsyncSession,
) -> None:
    if not message.text or not message.text.startswith("/track "):
        return await dialog_manager.start(
            AdminTrackSG.waiting_for_track,
            mode=StartMode.RESET_STACK,
        )

    track_query = message.text[len("/track ") :].strip()

    db_tracks = await track_service.search_tracks_by_query(
        session,
        track_query=track_query,
        limit=1,
    )

    if not db_tracks:
        await message.answer("Трек не найден")
        return None

    return await dialog_manager.start(
        AdminTrackSG.waiting_for_action,
        mode=StartMode.RESET_STACK,
        data={
            "track_id": db_tracks[0].id,
        },
    )
