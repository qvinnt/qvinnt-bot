from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_track_urls_keyboard(
    tiktok_url: str | None,
    youtube_url: str | None,
) -> InlineKeyboardMarkup:
    buttons = []
    if tiktok_url:
        buttons.append([InlineKeyboardButton(text="Смотреть в тиктоке 🟣", url=tiktok_url)])
    if youtube_url:
        buttons.append([InlineKeyboardButton(text="Смотреть на ютубе 🔴", url=youtube_url)])

    return InlineKeyboardMarkup(inline_keyboard=buttons)
