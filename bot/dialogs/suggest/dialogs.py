from __future__ import annotations

from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Cancel, Column, Select
from aiogram_dialog.widgets.text import Const, Format

from bot.dialogs.suggest import getters, handlers
from bot.states.suggest import SuggestSG

__TRACK_EXAMPLE = "<i>Пример: Cupsize - Ты любишь танцевать</i>"

suggest_dialog = Dialog(
    Window(
        Const(f"Введи название трека\n\n{__TRACK_EXAMPLE}"),
        Cancel(Const("Отмена"), when=F["start_data"]["first"]),
        Cancel(Const("« Назад"), when=~F["start_data"]["first"]),
        TextInput(
            "track",
            on_success=handlers.handle_track_input,
        ),
        state=SuggestSG.waiting_for_track,
    ),
    Window(
        Const("Выбери трек или введи название трека по-другому"),
        Column(
            Select(
                Format("{item[1][artist]} - {item[1][title]}"),
                id="tracks",
                item_id_getter=lambda x: x[0],
                items="tracks",
                on_click=handlers.handle_track_select,
                type_factory=lambda x: int(x),
            )
        ),
        TextInput(
            "track",
            on_success=handlers.handle_track_input,
        ),
        state=SuggestSG.waiting_for_confirmation,
        getter=getters.get_tracks_data,
    ),
)
