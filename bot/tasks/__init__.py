from __future__ import annotations

from typing import TYPE_CHECKING

from apscheduler.triggers.cron import CronTrigger

from bot.tasks.stats import stats_task

if TYPE_CHECKING:
    from aiogram import Bot
    from apscheduler.schedulers.base import BaseScheduler
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

    from bot.core.settings import Settings


def register_regular_tasks(
    scheduler: BaseScheduler,
    settings: Settings,
    sessionmaker: async_sessionmaker[AsyncSession],
    bot: Bot,
) -> None:
    scheduler.add_job(
        func=stats_task,
        trigger=CronTrigger.from_crontab(settings.tasks.stats_cron),
        kwargs={
            "sessionmaker": sessionmaker,
            "bot": bot,
            "admin_id": settings.bot.admin_id,
            "when": "yesterday",
        },
    )
