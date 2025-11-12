from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.filters import BaseFilter

if TYPE_CHECKING:
    from aiogram.types import Message

    from bot.core.settings import Settings


class AdminFilter(BaseFilter):
    async def __call__(
        self,
        message: Message,
        settings: Settings,
    ) -> bool:
        if message.from_user is None:
            return False

        return message.from_user.id == settings.bot.admin_id
