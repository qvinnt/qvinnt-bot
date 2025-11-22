from __future__ import annotations

from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class SuggestAnotherTrackCallbackData(CallbackData, prefix="suggest_another_track"):
    pass


SUGGEST_ANOTHER_TRACK_KEYBOARD = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Предложить другой трек",
                callback_data=SuggestAnotherTrackCallbackData().pack(),
            ),
        ]
    ],
)
