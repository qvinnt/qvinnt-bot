from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram_dialog import Data
from aiogram_dialog.widgets.kbd import Button
from loguru import logger

from bot.database.models import TrackModel
from bot.services import errors
from bot.services import track as track_service
from bot.services import vote as vote_service
from bot.services.lastfm import Track
from bot.states.admin.track import AdminTrackSG

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery, Message
    from aiogram_dialog import DialogManager
    from aiogram_dialog.widgets.input import ManagedTextInput
    from aiogram_dialog.widgets.kbd import Select
    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.services.lastfm import LastFmClient


async def handle_start(
    start_data: Any,
    dialog_manager: DialogManager,
) -> None:
    if isinstance(start_data, dict) and "track_id" in start_data:
        dialog_manager.dialog_data["track_id"] = start_data["track_id"]


async def handle_process_result(
    start_data: Data,
    result: Any,
    dialog_manager: DialogManager,
) -> None:
    if result == "deleted":
        await dialog_manager.done()


async def handle_track_input(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]

    db_tracks = await track_service.search_tracks_by_query(
        session,
        track_query=data,
        limit=1,
    )

    if not db_tracks:
        await message.answer("Трек не найден")
        return None

    db_track = db_tracks[0]
    dialog_manager.dialog_data["track_id"] = db_track.id

    return await dialog_manager.switch_to(AdminTrackSG.waiting_for_action)


async def handle_release_urls_input(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: list[str],
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]

    if not isinstance(dialog_manager.start_data, dict) or "track_id" not in dialog_manager.start_data:
        logger.error("Track id not found in start data")
        return await dialog_manager.done()

    update_functions = [
        track_service.update_track_tiktok_url,
        track_service.update_track_youtube_url,
    ]

    track_id = dialog_manager.start_data["track_id"]

    for url, update_function in zip(data, update_functions):
        if not url:
            continue

        await update_function(session, track_id, url)

    # TODO: Add notification task

    await message.answer("Трек зарелизен")
    return await dialog_manager.done()


async def handle_edit_artist_input(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]

    if not isinstance(dialog_manager.start_data, dict) or "track_id" not in dialog_manager.start_data:
        logger.error("Track id not found in start data")
        return await dialog_manager.done()

    track_id = dialog_manager.start_data["track_id"]

    try:
        await track_service.update_track_artist(session, track_id, data)
    except errors.TrackAlreadyExistsError:
        await message.answer("Трек с таким исполнителем и названием уже существует")
        return None
    except errors.TrackServiceError as e:
        logger.error(e)
        await message.answer("Произошла ошибка")
        return await dialog_manager.done()

    await message.answer("Исполнитель изменен")
    return await dialog_manager.done()


async def handle_edit_title_input(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]

    if not isinstance(dialog_manager.start_data, dict) or "track_id" not in dialog_manager.start_data:
        logger.error("Track id not found in start data")
        return await dialog_manager.done()

    track_id = dialog_manager.start_data["track_id"]

    try:
        await track_service.update_track_title(session, track_id, data)
    except errors.TrackAlreadyExistsError:
        await message.answer("Трек с таким исполнителем и названием уже существует")
        return None
    except errors.TrackServiceError as e:
        logger.error(e)
        await message.answer("Произошла ошибка")
        return await dialog_manager.done()

    await message.answer("Название изменено")
    return await dialog_manager.done()


async def handle_edit_tiktok_url_input(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]

    if not isinstance(dialog_manager.start_data, dict) or "track_id" not in dialog_manager.start_data:
        logger.error("Track id not found in start data")
        return await dialog_manager.done()

    track_id = dialog_manager.start_data["track_id"]

    try:
        await track_service.update_track_tiktok_url(session, track_id, data)
    except errors.TrackServiceError as e:
        logger.error(e)
        await message.answer("Произошла ошибка")
        return await dialog_manager.done()

    await message.answer("Ссылка на TikTok изменена")
    return await dialog_manager.done()


async def handle_edit_youtube_url_input(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]

    if not isinstance(dialog_manager.start_data, dict) or "track_id" not in dialog_manager.start_data:
        logger.error("Track id not found in start data")
        return await dialog_manager.done()

    track_id = dialog_manager.start_data["track_id"]

    try:
        await track_service.update_track_youtube_url(session, track_id, data)
    except errors.TrackServiceError as e:
        logger.error(e)
        await message.answer("Произошла ошибка")
        return await dialog_manager.done()

    await message.answer("Ссылка на YouTube изменена")
    return await dialog_manager.done()


async def handle_delete_confirmation_input(
    event: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]

    if not isinstance(dialog_manager.start_data, dict) or "track_id" not in dialog_manager.start_data:
        logger.error("Track id not found in start data")
        return await dialog_manager.done()

    track_id = dialog_manager.start_data["track_id"]

    try:
        await track_service.delete_track(session, track_id)
    except errors.TrackServiceError as e:
        logger.error(e)
        await event.message.answer("Произошла ошибка")
        return await dialog_manager.done()

    await event.message.answer("Трек удален")
    return await dialog_manager.done(result="deleted")
