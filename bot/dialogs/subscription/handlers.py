from __future__ import annotations

from typing import TYPE_CHECKING, Any

from bot.services import subscription as subscription_service

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery
    from aiogram_dialog import DialogManager
    from aiogram_dialog.widgets.kbd import Button
    from posthog import Posthog

    from bot.core.settings import Settings


async def handle_start(
    start_data: Any,
    dialog_manager: DialogManager,
) -> None:
    posthog: Posthog = dialog_manager.middleware_data["posthog"]
    posthog.capture(event="user faced subscription requirement")


async def handle_continue_button_click(
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
        await event.answer(
            f"Упс! Кажется, ты не подписан на мой канал @{settings.bot.subscription_channel.username}  👉👈",
            show_alert=True,
        )
        return None

    posthog: Posthog = dialog_manager.middleware_data["posthog"]
    posthog.capture(event="user passed subscription requirement")

    result = {
        "event": event,
    }
    result.update(dialog_manager.start_data or {})  # pyright: ignore[reportCallIssue, reportArgumentType]
    return await dialog_manager.done(result=result)
