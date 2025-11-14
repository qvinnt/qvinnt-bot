from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bot.dialogs.top.constants import TRACKS_PER_PAGE
from bot.services import track as track_service

if TYPE_CHECKING:
    from aiogram_dialog import DialogManager
    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.database.models import TrackModel


async def get_tracks_data(
    dialog_manager: DialogManager,
    **_: Any,
) -> dict[str, list[tuple[TrackModel, int]] | int]:
    session: AsyncSession = dialog_manager.middleware_data["session"]
    page = dialog_manager.dialog_data["page"]

    tracks = await track_service.get_tracks_by_votes(
        session,
        limit=TRACKS_PER_PAGE,
        offset=(page - 1) * TRACKS_PER_PAGE,
    )

    tracks_count = await track_service.get_tracks_count(session)

    return {
        "tracks": tracks,
        "max_pages": (tracks_count + TRACKS_PER_PAGE - 1) // TRACKS_PER_PAGE,
    }
