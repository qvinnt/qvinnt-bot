from __future__ import annotations

from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Back, Button, Cancel, Column, Select, SwitchTo, Url
from aiogram_dialog.widgets.text import Case, Const, Format, Jinja

from bot.dialogs.suggest import getters, handlers
from bot.states.suggest import SuggestSG

__TRACK_EXAMPLE = "<i>Пример:</i>\n<blockquote>Cupsize - Ты любишь танцевать</blockquote>"

suggest_dialog = Dialog(
    Window(
        Const(f"✍️ Напиши <b>автора</b> и <b>название</b> трека\n\n{__TRACK_EXAMPLE}"),
        Cancel(Const("Отмена"), when=F["start_data"]["first"]),
        Cancel(Const("« Назад"), when=~F["start_data"]["first"]),
        TextInput(
            "track",
            on_success=handlers.handle_track_input,
        ),
        state=SuggestSG.waiting_for_track,
    ),
    Window(
        Jinja("На трек <b>{{ artist }} - {{ title }}</b> уже есть кавер"),
        Column(
            Url(
                Const("Смотреть в тиктоке 🟣"),
                url=Format("{tiktok_url}"),
                id="view_in_tiktok",
                when=F["tiktok_url"],
            ),
            Url(
                Const("Смотреть на ютубе 🔴"),
                url=Format("{youtube_url}"),
                id="view_in_youtube",
                when=F["youtube_url"],
            ),
            Button(
                Const("Это не тот трек"),
                id="not_the_track",
                on_click=handlers.handle_not_the_track_button_click,
            ),
            Back(Const("« Назад")),
        ),
        state=SuggestSG.waiting_for_existing_done_track_action,
        getter=getters.get_existing_done_track_data,
    ),
    Window(
        Jinja("У трека <b>{{ artist }} - {{ title }}</b> уже <b>{{ votes_count }}</b> ⭐️"),
        Column(
            Button(
                Const("Проголосовать за этот трек ⭐️"),
                id="vote_for_existing_track",
                on_click=handlers.handle_vote_for_existing_track_button_click,
            ),
            Button(
                Const("Это не тот трек"),
                id="not_the_track",
                on_click=handlers.handle_not_the_track_button_click,
            ),
        ),
        state=SuggestSG.waiting_for_existing_not_done_track_action,
        getter=getters.get_existing_not_done_track_data,
    ),
    Window(
        Case(
            texts={
                True: Const(f"<b>Выбери трек</b> или <b>напиши трек</b> по-другому\n\n{__TRACK_EXAMPLE}"),
                False: Const(
                    f"😭 Ничего не нашел\nПопробуй <b>написать автора</b> и <b>название</b> трека по-другому\n\n{__TRACK_EXAMPLE}"  # noqa: E501
                ),
            },
            selector=F["tracks"].func(lambda x: len(x) > 0),
        ),
        Column(
            Select(
                Format("{item[1][artist]} - {item[1][title]}"),
                id="tracks",
                item_id_getter=lambda x: x[0],
                items="tracks",
                on_click=handlers.handle_new_track_select,
                type_factory=lambda x: int(x),
            )
        ),
        SwitchTo(
            Const("« Назад"),
            id="back",
            state=SuggestSG.waiting_for_track,
        ),
        TextInput(
            "track",
            on_success=handlers.handle_track_input,
        ),
        state=SuggestSG.waiting_for_new_track_selection,
        getter=getters.get_new_tracks_data,
    ),
)
