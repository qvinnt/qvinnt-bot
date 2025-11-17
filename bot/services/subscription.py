from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.enums import ChatMemberStatus

if TYPE_CHECKING:
    from aiogram import Bot


async def is_subscribed(bot: Bot, chat_id: int, user_id: int) -> bool:
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]
