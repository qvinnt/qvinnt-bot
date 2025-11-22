from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from loguru import logger

from bot.services import track as track_service
from bot.services import user as user_service
from bot.services import vote as vote_service

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
        "tiktok_url": "",
        "youtube_url": "",
        "votes_count": 0,
        "suggested_by_name": "",
        "suggested_by_id": 0,
        "suggested_at": "",
        "deny_reason": "",
    }

    track = await track_service.get_track_by_id(session, track_id)
    if not track:
        logger.error(f"Track with id {track_id} not found")
        return data

    votes_count = await vote_service.get_votes_count_by_track(session, track_id)
    votes = await vote_service.get_votes_by_track(session, track_id, limit=1)
    if votes:
        user = await user_service.get_user(session, votes[0].user_id)
        if user:
            data["suggested_by_name"] = user.full_name
            data["suggested_by_id"] = user.id
            data["suggested_at"] = votes[0].created_at.astimezone(datetime.timezone(datetime.timedelta(hours=3)))

    data["artist"] = track.artist
    data["title"] = track.title
    data["tiktok_url"] = track.tiktok_url or ""
    data["youtube_url"] = track.youtube_url or ""
    data["votes_count"] = votes_count
    data["deny_reason"] = track.deny_reason or ""

    return data


async def get_release_delays(
    **_: Any,
) -> dict[str, list[list[int | str]]]:
    return {
        "delays": [
            ["0", "Рассылка сразу"],
            ["1", "Рассылка через 1 минуту"],
            ["3", "Рассылка через 3 минуты"],
            ["5", "Рассылка через 5 минут"],
        ],
    }


async def get_deny_reason(
    dialog_manager: DialogManager,
    **_: Any,
) -> dict[str, str]:
    return {
        "reason": dialog_manager.dialog_data["reason"],
    }
