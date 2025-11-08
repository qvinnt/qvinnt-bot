from __future__ import annotations

from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Column, Counter, Select, Start
from aiogram_dialog.widgets.text import Const, Format

from bot.dialogs.top import getters, handlers
from bot.states.suggest import SuggestSG
from bot.states.top import TopSG

top_dialog = Dialog(
    Window(
        Const("""
🥁 Снимаю <b>каверы</b> на треки с <b>наибольшим количеством голосов ⭐️</b>

Нажимай на трек, чтобы <b>проголосовать ⭐️</b> за него
"""),
        Column(
            Select(
                Format("{item[0].artist} - {item[0].title} | {item[1]} ⭐️"),
                id="tracks",
                item_id_getter=lambda x: x[0].id,
                items="tracks",
                on_click=handlers.handle_track_select,
                type_factory=lambda x: int(x),
            ),
        ),
        Counter(
            id="page",
            default=1,
            min_value=1,
            plus=Const(">"),
            minus=Const("<"),
            on_value_changed=handlers.handle_page_change,
        ),
        Start(
            Const("Предложить другой трек"),
            id="suggest_track",
            state=SuggestSG.waiting_for_track,
            data={
                "first": False,
            },
        ),
        state=TopSG.waiting_for_action,
        getter=getters.get_tracks_data,
    ),
    on_start=handlers.handle_start,
)
