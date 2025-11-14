from __future__ import annotations

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

SUGGEST_BUTTON = KeyboardButton(text="Предложить трек")
TOP_BUTTON = KeyboardButton(text="Топ треков")


MAIN_KEYBOARD = ReplyKeyboardMarkup(
    keyboard=[
        [
            SUGGEST_BUTTON,
            TOP_BUTTON,
        ]
    ],
    resize_keyboard=True,
)
