from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aiogram_dialog import DialogManager

    from bot.core.settings import Settings


async def get_data(
    dialog_manager: DialogManager,
    settings: Settings,
    **_: Any,
) -> dict[str, str]:
    return {
        "username": settings.bot.subscription_channel.username,
        "invite_url": settings.bot.subscription_channel.invite_url,
    }
