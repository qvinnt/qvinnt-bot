from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger

from bot.services import errors
from bot.services import subscription as subscription_service
from bot.services import track as track_service
from bot.services import vote as vote_service
from bot.services.lastfm import Track
from bot.states.subscription import SubscriptionSG
from bot.states.suggest import SuggestSG

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery, Message
    from aiogram_dialog import Data, DialogManager
    from aiogram_dialog.widgets.input import ManagedTextInput
    from aiogram_dialog.widgets.kbd import Button, Select
    from posthog import Posthog
    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.core.settings import Settings
    from bot.services.lastfm import LastFmClient


__LAST_FM_SEARCH_LIMIT = 3


async def handle_track_input(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
) -> None:
    session: AsyncSession = dialog_manager.middleware_data["session"]

    dialog_manager.dialog_data["track_query"] = data

    db_tracks = await track_service.search_tracks_by_query(
        session,
        track_query=data,
        limit=1,
    )

    if db_tracks:
        db_track = db_tracks[0]
        dialog_manager.dialog_data["track_id"] = db_track.id
        dialog_manager.dialog_data["title"] = db_track.title
        dialog_manager.dialog_data["artist"] = db_track.artist

        if db_track.is_used:
            return await dialog_manager.switch_to(SuggestSG.waiting_for_existing_done_track_action)

        return await dialog_manager.switch_to(SuggestSG.waiting_for_existing_not_done_track_action)

    artist_name = None
    song_name = data

    if "-" in data:
        parts = data.split("-", 1)
        if len(parts) == 2 and parts[0].strip() and parts[1].strip():  # noqa: PLR2004
            artist_name = parts[0].strip()
            song_name = parts[1].strip()

    last_fm_client: LastFmClient = dialog_manager.middleware_data["last_fm_client"]
    lastfm_tracks = await last_fm_client.search_tracks(
        song_name=song_name,
        artist_name=artist_name,
        limit=__LAST_FM_SEARCH_LIMIT,
    )

    if not lastfm_tracks and artist_name and song_name:
        lastfm_tracks = await last_fm_client.search_tracks(
            song_name=artist_name,
            artist_name=song_name,
            limit=__LAST_FM_SEARCH_LIMIT,
        )

    dialog_manager.dialog_data["tracks"] = [track.model_dump() for track in lastfm_tracks]

    return await dialog_manager.switch_to(SuggestSG.waiting_for_new_track_selection)


async def handle_not_the_track_button_click(
    event: CallbackQuery,
    button: Button,
    dialog_manager: DialogManager,
) -> None:
    track_query = dialog_manager.dialog_data["track_query"]

    artist = None
    title = track_query

    if "-" in track_query:
        parts = track_query.split("-", 1)
        if len(parts) == 2 and parts[0].strip() and parts[1].strip():  # noqa: PLR2004
            artist = parts[0].strip()
            title = parts[1].strip()

    last_fm_client: LastFmClient = dialog_manager.middleware_data["last_fm_client"]
    lastfm_tracks = await last_fm_client.search_tracks(
        song_name=title,
        artist_name=artist,
        limit=__LAST_FM_SEARCH_LIMIT,
    )

    if not lastfm_tracks and artist and title:
        lastfm_tracks = await last_fm_client.search_tracks(
            song_name=artist,
            artist_name=title,
            limit=__LAST_FM_SEARCH_LIMIT,
        )

    if lastfm_tracks:
        dialog_manager.dialog_data["tracks"] = [track.model_dump() for track in lastfm_tracks]
        return await dialog_manager.switch_to(SuggestSG.waiting_for_new_track_selection)

    return await dialog_manager.switch_to(SuggestSG.waiting_for_new_track_selection)


async def handle_waiting_for_existing_not_done_track_action_process_result(
    start_data: Data,
    result: Any,
    dialog_manager: DialogManager,
) -> None:
    if not isinstance(result, dict):
        return

    event = result["event"]

    await handle_vote_for_existing_track_button_click(
        event=event,
        button=None,  # pyright: ignore[reportArgumentType]
        dialog_manager=dialog_manager,
    )


async def handle_vote_for_existing_track_button_click(
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
    artist = dialog_manager.dialog_data["artist"]
    title = dialog_manager.dialog_data["title"]

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

    await send_vote_success_message(
        message=event.message,
        track_id=track_id,
        artist=artist,
        title=title,
    )

    return await dialog_manager.done()


async def handle_waiting_for_new_track_selection_process_result(
    start_data: Data,
    result: Any,
    dialog_manager: DialogManager,
) -> None:
    if not isinstance(result, dict):
        return

    event = result["event"]
    track_id = result["track_id"]

    await handle_new_track_select(
        event=event,
        select=None,  # pyright: ignore[reportArgumentType]
        dialog_manager=dialog_manager,
        data=track_id,
    )


async def handle_new_track_select(
    event: CallbackQuery,
    select: Select[int],
    dialog_manager: DialogManager,
    data: int,
) -> None:
    settings: Settings = dialog_manager.middleware_data["settings"]

    is_subscribed = await subscription_service.is_subscribed(
        event.bot,
        settings.bot.subscription_channel.id,
        event.from_user.id,
    )
    if not is_subscribed:
        return await dialog_manager.start(
            SubscriptionSG.waiting_for_action,
            data={
                "track_id": data,
            },
        )

    session: AsyncSession = dialog_manager.middleware_data["session"]
    track_data: Track = Track.model_validate(dialog_manager.dialog_data["tracks"][data])

    try:
        track = await track_service.create_track(
            session,
            title=track_data.title,
            artist=track_data.artist,
        )
    except errors.TrackAlreadyExistsError:
        track = await track_service.get_track_by_title_and_artist(
            session,
            title=track_data.title,
            artist=track_data.artist,
        )

        if track is None:
            logger.error(f"Track not found for title {track_data.title} and artist {track_data.artist}")
            await event.answer("⚠️ Произошла ошибка", show_alert=True)
            return None

        if track.is_used:
            return await dialog_manager.switch_to(SuggestSG.waiting_for_existing_done_track_action)

        try:
            await vote_service.create_vote(
                session,
                user_id=event.from_user.id,
                track_id=track.id,
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

        await send_vote_success_message(
            message=event.message,
            track_id=track.id,
            artist=track.artist,
            title=track.title,
        )

        return await dialog_manager.done()
    except errors.ServiceError as e:
        logger.error(e)
        await event.answer("⚠️ Произошла ошибка", show_alert=True)
        return None

    try:
        await vote_service.create_vote(
            session,
            user_id=event.from_user.id,
            track_id=track.id,
        )
    except errors.ServiceError as e:
        logger.error(e)
        await event.answer("⚠️ Произошла ошибка", show_alert=True)
        return None
    else:
        posthog: Posthog = dialog_manager.middleware_data["posthog"]
        posthog.capture(event="vote created")

    await send_vote_success_message(
        message=event.message,
        track_id=track.id,
        artist=track.artist,
        title=track.title,
    )

    return await dialog_manager.done()


async def send_vote_success_message(
    message: Message,
    track_id: int,
    artist: str,
    title: str,
) -> None:
    text = f"""
Вы проголосовали за трек ⭐️
<b>{artist} - {title}</b>

Делись ссылкой на трек, чтобы он собрал больше голосов
<code>t.me/{(await message.bot.get_me()).username}?start=vote_{track_id}</code>
"""
    await message.answer(text)
