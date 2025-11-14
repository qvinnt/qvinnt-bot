from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from bot.services import track as track_service

if TYPE_CHECKING:
    from aiogram_dialog import DialogManager
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_track_data(
    dialog_manager: DialogManager,
    **_: Any,
) -> dict[str, str]:
    session: AsyncSession = dialog_manager.middleware_data["session"]
    track_id = dialog_manager.dialog_data["track_id"]

    data = {
        "artist": "",
        "title": "",
    }

    track = await track_service.get_track_by_id(session, track_id)
    if track is None:
        logger.error(f"Track with id {track_id} not found")
        return data

    data["artist"] = track.artist
    data["title"] = track.title

    return data
