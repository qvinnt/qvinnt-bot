from __future__ import annotations

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Cancel, Column
from aiogram_dialog.widgets.text import Const, Jinja

from bot.dialogs.vote import getters, handlers
from bot.states.vote import VoteSG

vote_dialog = Dialog(
    Window(
        Jinja("""
Хотите проголосовать за трек <b>{{ artist }} - {{ title }}</b> ⭐️

<i>Чем больше голосов, тем больше вероятность, что на этот трек появится кавер</i>"""),
        Column(
            Button(
                Const("Да, хочу"),
                id="yes",
                on_click=handlers.handle_vote_button_click,
            ),
            Cancel(Const("Нет, не хочу ")),
        ),
        state=VoteSG.waiting_for_action,
        getter=getters.get_track_data,
    ),
    on_start=handlers.handle_on_start,
)
