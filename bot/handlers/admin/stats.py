from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import Command

from bot.tasks.stats import stats_task

if TYPE_CHECKING:
    from aiogram import types
    from aiogram_dialog import DialogManager
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from bot.core.settings import Settings

router = Router(name=__name__)


@router.message(Command("stats"))
async def handle_stats_command(
    message: types.Message,
    dialog_manager: DialogManager,
    scheduler: AsyncIOScheduler,
    settings: Settings,
    sessionmaker: async_sessionmaker[AsyncSession],
) -> None:
    scheduler.add_job(
        stats_task,
        trigger="date",
        kwargs={
            "sessionmaker": sessionmaker,
            "bot": message.bot,
            "admin_id": settings.bot.admin_id,
            "when": "today",
        },
    )
