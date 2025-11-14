from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from bot.services import track as track_service
from bot.services import vote as vote_service

if TYPE_CHECKING:
    from aiogram_dialog import DialogManager
    from sqlalchemy.ext.asyncio import AsyncSession


async def get_existing_done_track_data(
    dialog_manager: DialogManager,
    **_: Any,
) -> dict[str, str]:
    session: AsyncSession = dialog_manager.middleware_data["session"]
    track_id = dialog_manager.dialog_data["track_id"]

    data = {
        "artist": "",
        "title": "",
        "tiktok_url": "",
        "youtube_url": "",
    }

    track = await track_service.get_track_by_id(session, track_id)
    if track is None:
        logger.error(f"Track with id {track_id} not found")
        return data

    data["artist"] = track.artist
    data["title"] = track.title
    data["tiktok_url"] = track.tiktok_url or ""
    data["youtube_url"] = track.youtube_url or ""

    return data


async def get_existing_not_done_track_data(
    dialog_manager: DialogManager,
    **_: Any,
) -> dict[str, str | int]:
    session: AsyncSession = dialog_manager.middleware_data["session"]
    track_id = dialog_manager.dialog_data["track_id"]

    data = {
        "artist": "",
        "title": "",
        "votes_count": 0,
    }

    track = await track_service.get_track_by_id(session, track_id)
    if track is None:
        logger.error(f"Track with id {track_id} not found")
        return data

    data["artist"] = track.artist
    data["title"] = track.title
    data["votes_count"] = await vote_service.get_votes_count_by_track(session, track_id)

    return data


async def get_new_tracks_data(
    dialog_manager: DialogManager,
    **_: Any,
) -> dict[str, list[tuple[int, dict]]]:
    tracks = dialog_manager.dialog_data["tracks"]
    return {
        "tracks": list(enumerate(tracks)),
    }
