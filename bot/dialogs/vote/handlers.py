from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from bot.dialogs.suggest.handlers import send_vote_success_message
from bot.services import errors
from bot.services import track as track_service
from bot.services import vote as vote_service

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery
    from aiogram_dialog import DialogManager
    from aiogram_dialog.widgets.kbd import Button
    from sqlalchemy.ext.asyncio import AsyncSession



async def handle_on_start(
    start_data: Any,
    dialog_manager: DialogManager,
) -> None:
    if not isinstance(start_data, dict) or "track_id" not in start_data:
        logger.error("Invalid start data")
        return

    dialog_manager.dialog_data["track_id"] = start_data["track_id"]


async def handle_vote_button_click(
    event: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]
    track_id = dialog_manager.dialog_data["track_id"]

    try:
        await vote_service.create_vote(
            session,
            user_id=event.from_user.id,
            track_id=track_id,
        )
    except errors.VoteAlreadyExistsError:
        await event.answer("Вы уже проголосовали за этот трек", show_alert=True)
        return await dialog_manager.done()
    except errors.ServiceError as e:
        logger.error(e)
        await event.answer("⚠️ Произошла ошибка", show_alert=True)
        return None

    track = await track_service.get_track_by_id(session, track_id)
    if track is None:
        logger.error(f"Track with id {track_id} not found")
        await event.answer("⚠️ Произошла ошибка", show_alert=True)
        return None

    await send_vote_success_message(
        message=event.message,
        track_id=track.id,
        artist=track.artist,
        title=track.title,
    )

    return await dialog_manager.done()
