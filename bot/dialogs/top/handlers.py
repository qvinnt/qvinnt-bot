from __future__ import annotations

from typing import TYPE_CHECKING, Any

from aiogram_dialog.widgets.kbd import ManagedCounter
from loguru import logger

from bot.services import errors
from bot.services import track as track_service
from bot.services import vote as vote_service
from bot.services.lastfm import Track
from bot.states.suggest import SuggestSG

if TYPE_CHECKING:
    from aiogram.types import CallbackQuery, Message
    from aiogram_dialog import DialogManager
    from aiogram_dialog.widgets.input import ManagedTextInput
    from aiogram_dialog.widgets.kbd import Select
    from sqlalchemy.ext.asyncio import AsyncSession

    from bot.services.lastfm import LastFmClient


async def handle_start(
    start_data: Any,
    dialog_manager: DialogManager,
) -> None:
    dialog_manager.dialog_data["page"] = 1


async def handle_page_change(
    event: CallbackQuery,
    widget: ManagedCounter,
    dialog_manager: DialogManager,
) -> None:
    page = widget.get_value()
    dialog_manager.dialog_data["page"] = page
