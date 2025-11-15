from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from aiogram.exceptions import AiogramError
from loguru import logger

from bot.keyboards.inline.track_urls import get_track_urls_keyboard
from bot.services import errors
from bot.services import track as track_service
from bot.services import vote as vote_service
from bot.states.admin.track import AdminTrackSG

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.types import CallbackQuery, Message
    from aiogram_dialog import Data, DialogManager
    from aiogram_dialog.widgets.input import ManagedTextInput
    from aiogram_dialog.widgets.kbd import Button
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.core.settings import Settings
    from bot.database.models import TrackModel


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

    for url, update_function in zip(data, update_functions, strict=False):
        if not url:
            continue

        await update_function(session, track_id, url)

    track = await track_service.get_track_by_id(session, track_id)
    if not track:
        logger.error(f"Track with id {track_id} not found")
        await message.answer("Трек не найден")
        return await dialog_manager.done()

    scheduler: AsyncIOScheduler = dialog_manager.middleware_data["scheduler"]
    settings: Settings = dialog_manager.middleware_data["settings"]
    scheduler.add_job(
        __send_notification_about_new_track,
        trigger="date",
        kwargs={
            "session": session,
            "bot": message.bot,
            "track": track,
            "admin_id": settings.bot.admin_id,
        },
    )

    await message.answer("Трек зарелизен")
    return await dialog_manager.done()


async def __send_notification_about_new_track(
    session: AsyncSession,
    bot: Bot,
    track: TrackModel,
    admin_id: int,
) -> None:
    votes = await vote_service.get_votes_by_track(session, track.id)

    await bot.send_message(
        admin_id, f"Рассылка о треке {track.artist} - {track.title} на {len(votes)} человек запущена"
    )

    text = f"На трек <b>{track.artist} - {track.title}</b> вышел кавер"
    keyboard = get_track_urls_keyboard(track.tiktok_url, track.youtube_url)

    for vote in votes:
        try:
            await bot.send_message(
                vote.user_id,
                text,
                reply_markup=keyboard,
            )
        except AiogramError as e:
            logger.warning(f"Error sending message to user {vote.user_id}: {e}")
        await asyncio.sleep(0.5)

    await bot.send_message(admin_id, f"Рассылка о треке {track.artist} - {track.title} завершена")


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
