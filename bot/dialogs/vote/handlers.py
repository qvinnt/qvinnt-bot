from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from bot.dialogs.suggest.handlers import send_vote_success_message
from bot.services import errors
from bot.services import subscription as subscription_service
from bot.services import track as track_service
from bot.services import vote as vote_service
from bot.states.subscription import SubscriptionSG

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery
    from aiogram_dialog import Data, DialogManager
    from aiogram_dialog.widgets.kbd import Button
    from posthog import Posthog
    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.core.settings import Settings


async def handle_on_start(
    start_data: Any,
    dialog_manager: DialogManager,
) -> None:
    if not isinstance(start_data, dict) or "track_id" not in start_data:
        logger.error("Invalid start data")
        return

    dialog_manager.dialog_data["track_id"] = start_data["track_id"]


async def handle_process_result(
    start_data: Data,
    result: Any,
    dialog_manager: DialogManager,
) -> None:
    if not isinstance(result, dict):
        return

    event = result["event"]

    await handle_vote_button_click(
        event=event,
        button=None,  # pyright: ignore[reportArgumentType]
        dialog_manager=dialog_manager,
    )


async def handle_vote_button_click(
    event: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    settings: Settings = dialog_manager.middleware_data["settings"]

    is_subscribed = await subscription_service.is_subscribed(
        event.bot,
        settings.bot.subscription_channel.id,
        event.from_user.id,
    )
    if not is_subscribed:
        return await dialog_manager.start(SubscriptionSG.waiting_for_action)

    session: AsyncSession = dialog_manager.middleware_data["session"]
    track_id = dialog_manager.dialog_data["track_id"]

    try:
        await vote_service.create_vote(
            session,
            user_id=event.from_user.id,
            track_id=track_id,
        )
    except errors.VoteAlreadyExistsError:
        await event.answer("Вы уже голосовали за этот трек", show_alert=True)
        return await dialog_manager.done()
    except errors.ServiceError as e:
        logger.error(e)
        await event.answer("⚠️ Произошла ошибка", show_alert=True)
        return None
    else:
        posthog: Posthog = dialog_manager.middleware_data["posthog"]
        posthog.capture(event="vote created")

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
