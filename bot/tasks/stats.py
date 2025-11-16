from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Literal

from bot.database.utils import with_session_context
from bot.services import track as track_service
from bot.services import user as user_service
from bot.services import vote as vote_service

if TYPE_CHECKING:
    from aiogram import Bot
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


_MOSCOW_TZ = datetime.timezone(datetime.timedelta(hours=3))


async def stats_task(
    sessionmaker: async_sessionmaker[AsyncSession],
    bot: Bot,
    admin_id: int,
    when: Literal["yesterday", "today"] = "yesterday",
) -> None:
    async def _stats_with_session(session: AsyncSession) -> None:
        if when == "yesterday":
            date = datetime.datetime.now(_MOSCOW_TZ).replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - datetime.timedelta(days=1)
        elif when == "today":
            date = datetime.datetime.now(_MOSCOW_TZ).replace(hour=0, minute=0, second=0, microsecond=0)

        users_count = await user_service.get_users_count(session)
        users_count_one_day = await user_service.get_users_count(session, created_from=date)
        votes_count_one_day = await vote_service.get_votes_count(session, created_from=date)
        tracks_count = await track_service.get_tracks_count(session, skip_used=False)
        tracks_count_one_day = await track_service.get_tracks_count(session, created_from=date)

        text = f"""
<b>Статистика за {date.strftime("%d.%m.%Y")}</b>

👥 <b>Пользователи</b>
<blockquote>Всего: <b>{users_count}</b>
Новых: <b>{users_count_one_day}</b></blockquote>

⭐️ <b>Голоса</b>
<blockquote>Новых: <b>{votes_count_one_day}</b></blockquote>

🎵 <b>Треки</b>
<blockquote>Всего незарелизенных: <b>{tracks_count}</b>
Новых: <b>{tracks_count_one_day}</b></blockquote>
"""
        await bot.send_message(chat_id=admin_id, text=text)

    await with_session_context(sessionmaker, _stats_with_session)
