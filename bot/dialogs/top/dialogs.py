from __future__ import annotations

from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Column, Counter, Select, Start
from aiogram_dialog.widgets.text import Case, Const, Format

from bot.dialogs.custom_widgets import TrackText
from bot.dialogs.top import getters, handlers
from bot.states.suggest import SuggestSG
from bot.states.top import TopSG

top_dialog = Dialog(
    Window(
        Case(
            texts={
                True: Const(
                    """🥁 Снимаю <b>каверы</b> на треки у которых <b>много</b> ⭐️

Нажми на трек, чтобы <b>проголосовать ⭐️</b>""",
                ),
                False: Const("Сейчас нет предложенных треков"),
            },
            selector=F["tracks"].func(lambda x: len(x) > 0),
        ),
        Column(
            Select(
                TrackText(
                    item="item",
                    track_getter=lambda x: x[0],
                    votes_getter=lambda x: x[1],
                ),
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
            text=Format("{value:g}/{data[max_pages]}"),
            on_value_changed=handlers.handle_page_change,
            when=F["max_pages"] > 1,
        ),
        Start(
            Case(
                texts={
                    True: Const("Предложить другой трек"),
                    False: Const("Предложить трек"),
                },
                selector=F["tracks"].func(lambda x: len(x) > 0),
            ),
            id="suggest_track",
            state=SuggestSG.waiting_for_track,
            data={
                "first": False,
            },
        ),
        state=TopSG.waiting_for_action,
        getter=getters.get_tracks_data,
        on_process_result=handlers.handle_process_result,
    ),
    on_start=handlers.handle_start,
)
