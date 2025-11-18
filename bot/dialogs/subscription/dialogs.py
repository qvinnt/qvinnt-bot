from __future__ import annotations

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Jinja

from bot.dialogs.subscription import getters, handlers
from bot.states.subscription import SubscriptionSG

subscription_dialog = Dialog(
    Window(
        Jinja(
            "Подпишись на мой канал <b><a href='{{ invite_url }}'>@{{ username }}</a></b>, чтобы проголосовать за трек"
        ),
        Button(
            Const("Проголосовать ⭐️"),
            id="continue",
            on_click=handlers.handle_continue_button_click,
        ),
        getter=getters.get_data,
        state=SubscriptionSG.waiting_for_action,
    ),
    on_start=handlers.handle_start,
)
