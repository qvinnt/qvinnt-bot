from __future__ import annotations

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Cancel, Select
from aiogram_dialog.widgets.text import Const, Jinja

from bot.dialogs.suggest import getters, handlers
from bot.states.suggest import SuggestSG

__TRACK_EXAMPLE = "<i>Пример: Cupsize - Ты любишь танцевать</i>"

suggest_dialog = Dialog(
    Window(
        Const(f"Введите название трека\n\n{__TRACK_EXAMPLE}"),
        Cancel(Const("Отмена")),
        TextInput(
            "track",
            on_success=handlers.handle_track_input,
        ),
        state=SuggestSG.waiting_for_track,
    ),
    Window(
        Const(f"Выберите трек или введите название трека по-другому\n\n{__TRACK_EXAMPLE}"),
        Select(
            Jinja("{{item[1].artist}} - {{item[1].song}}"),
            id="tracks",
            item_id_getter=lambda x: x[0],
            items="tracks",
            on_click=handlers.handle_track_select,
        ),
        TextInput(
            "track",
            on_success=handlers.handle_track_input,
        ),
        state=SuggestSG.waiting_for_confirmation,
        getter=getters.get_tracks_data,
    ),
)
