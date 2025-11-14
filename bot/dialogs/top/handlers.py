from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from bot.dialogs.top.constants import TRACKS_PER_PAGE
from bot.services import errors
from bot.services import track as track_service
from bot.services import vote as vote_service
from bot.states.admin.track import AdminTrackSG

if TYPE_CHECKING:
    from aiogram_dialog import ChatEvent, DialogManager
    from aiogram_dialog.widgets.kbd import ManagedCounter, Select
    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.core.settings import Settings


async def handle_start(
    start_data: Any,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["page"] = 1
    session: AsyncSession = dialog_manager.middleware_data["session"]
    tracks_count = await track_service.get_tracks_count(session)
    dialog_manager.dialog_data["max_pages"] = (tracks_count + TRACKS_PER_PAGE - 1) // TRACKS_PER_PAGE or 1


async def handle_page_change(
    event: ChatEvent,
    counter: ManagedCounter,
    dialog_manager: DialogManager,
) -> None:
    page = counter.get_value()
    max_pages = dialog_manager.dialog_data["max_pages"]

    if page > max_pages:
        await counter.set_value(max_pages)
        return

    dialog_manager.dialog_data["page"] = page


async def handle_track_select(
    event: ChatEvent,
    select: Select[int],
    dialog_manager: DialogManager,
    data: int,
) -> None:
    settings: Settings = dialog_manager.middleware_data["settings"]
    if event.from_user.id == settings.bot.admin_id:
        return await dialog_manager.start(
            AdminTrackSG.waiting_for_action,
            data={
                "track_id": data,
            },
        )

    session: AsyncSession = dialog_manager.middleware_data["session"]

    try:
        await vote_service.create_vote(
            session,
            user_id=event.from_user.id,  # pyright: ignore[reportOptionalMemberAccess]
            track_id=data,
        )
    except errors.VoteAlreadyExistsError:
        await event.answer("Вы уже проголосовали за этот трек", show_alert=True)  # pyright: ignore[reportAttributeAccessIssue]
        return None
    except errors.ServiceError as e:
        logger.error(e)
        await event.answer("⚠️ Произошла ошибка", show_alert=True)  # pyright: ignore[reportAttributeAccessIssue]
        return None
    else:
        await event.answer("⭐️ Вы проголосовали за трек")  # pyright: ignore[reportAttributeAccessIssue]
