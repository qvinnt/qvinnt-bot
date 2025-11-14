from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import Router
from aiogram.filters import ExceptionTypeFilter
from aiogram_dialog.api.exceptions import NoContextError, UnknownIntent, UnknownState
from loguru import logger

if TYPE_CHECKING:
    from aiogram import types

router = Router(name=__name__)


@router.error(ExceptionTypeFilter(UnknownIntent, UnknownState, NoContextError))
async def handle_unknown_intent(
    event: types.ErrorEvent,
) -> None:
    if not event.update.callback_query:
        logger.error("callback query is missing in the event")
        return

    await event.update.callback_query.answer(
        "Кнопка устарела. Введите команду заного.",
        show_alert=True,
    )
