from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import BotCommand, BotCommandScopeAllPrivateChats, BotCommandScopeChat

if TYPE_CHECKING:
    from aiogram import Bot

default_commands = [
    BotCommand(command="suggest", description="🎵 Предложить трек"),
    BotCommand(command="top", description="🏆 Топ треков"),
]

admin_commands = [
    BotCommand(command="track", description="⚙️ Настройки трека"),
]


async def set_commands(bot: Bot, admin_id: int) -> None:
    await bot.set_my_commands(
        commands=default_commands,
        scope=BotCommandScopeAllPrivateChats(),
    )
    await bot.set_my_commands(
        commands=default_commands + admin_commands,
        scope=BotCommandScopeChat(chat_id=admin_id),
    )


async def remove_commands(bot: Bot, admin_id: int) -> None:
    await bot.delete_my_commands(scope=BotCommandScopeAllPrivateChats())
    await bot.delete_my_commands(scope=BotCommandScopeChat(chat_id=admin_id))
