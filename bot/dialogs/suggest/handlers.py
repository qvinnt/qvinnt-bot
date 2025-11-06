from __future__ import annotations

from typing import TYPE_CHECKING

from loguru import logger

from bot.services import errors
from bot.services import track as track_service
from bot.services import vote as vote_service
from bot.states.suggest import SuggestSG

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery, Message
    from aiogram_dialog import DialogManager
    from aiogram_dialog.widgets.input import ManagedTextInput
    from aiogram_dialog.widgets.kbd import Select
    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.services.lastfm import LastFmClient, Track


__SEARCH_LIMIT = 3


async def handle_track_input(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    data: str,
) -> None:
    last_fm_client: LastFmClient = dialog_manager.middleware_data["last_fm_client"]

    if "-" in data and len(data.split("-")) == 2:  # noqa: PLR2004
        artist_name, song_name = data.split("-")
        tracks = await last_fm_client.search_tracks(
            song_name=song_name,
            artist_name=artist_name,
            limit=__SEARCH_LIMIT,
        )
    else:
        tracks = await last_fm_client.search_tracks(
            song_name=data,
            limit=__SEARCH_LIMIT,
        )

    dialog_manager.dialog_data["tracks"] = tracks

    await dialog_manager.switch_to(SuggestSG.waiting_for_confirmation)


async def handle_track_select(
    event: CallbackQuery,
    select: Select[int],
    dialog_manager: DialogManager,
    data: int,
) -> None:
    session: AsyncSession = dialog_manager.dialog_data["session"]
    track_data: Track = dialog_manager.dialog_data["tracks"][data]

    try:
        track = await track_service.create_track(
            session,
            title=track_data.title,
            artist=track_data.artist,
        )
    except errors.ServiceError as e:
        logger.error(e)
        await event.answer("⚠️ Произошла ошибка")
        return None

    try:
        await vote_service.create_vote(
            session,
            user_id=event.from_user.id,
            track_id=track.id,
        )
    except errors.ServiceError as e:
        logger.error(e)
        await event.answer("⚠️ Произошла ошибка")
        return None

    text = f"""
✨ Вы проголосовали за трек <b>{track.artist} - {track.title}</b>

Поделись ссылкой для голосования за этот трек:
<code>t.me/{(await event.bot.get_me()).username}?start=vote_{track.id}</code>
"""
    await event.message.answer(text)

    return dialog_manager.done()
