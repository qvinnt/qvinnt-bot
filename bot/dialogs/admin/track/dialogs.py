from __future__ import annotations

from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.kbd import Button, Cancel, Column, Group, Toggle
from aiogram_dialog.widgets.text import Const, Format, Jinja

from bot.dialogs.admin.track import getters, handlers
from bot.dialogs.custom_widgets import StartWithData
from bot.states.admin.track import (
    AdminTrackDeleteSG,
    AdminTrackEditArtistSG,
    AdminTrackEditTiktokUrlSG,
    AdminTrackEditTitleSG,
    AdminTrackEditYoutubeUrlSG,
    AdminTrackReleaseSG,
    AdminTrackSG,
)

__TRACK_EXAMPLE = "<i>Пример:</i>\n<blockquote>Cupsize - Ты любишь танцевать</blockquote>"

admin_track_dialog = Dialog(
    Window(
        Const(f"Введи название трека\n\n{__TRACK_EXAMPLE}"),
        Cancel(Const("Отмена")),
        TextInput(
            "track",
            on_success=handlers.handle_track_input,
        ),
        state=AdminTrackSG.waiting_for_track,
    ),
    Window(
        Jinja("""Исполнитель: <b>{{ artist }}</b>
Название: <b>{{ title }}</b>

Голосов: <b>{{ votes_count }}</b> ⭐

{% if suggested_by_id %}
Предложено: <b><a href='tg://user?id={{ suggested_by_id }}'>{{ suggested_by_name }}</a></b>
Дата предложения: <b>{{ suggested_at.strftime("%d.%m.%Y %H:%M") }}</b>
{% endif %}

🟣 TikTok: <b>{{ tiktok_url or "—" }}</b>
🔴 YouTube: <b>{{ youtube_url or "—" }}</b>"""),
        StartWithData(
            Const("Зарелизить"),
            id="release",
            state=AdminTrackReleaseSG.waiting_for_urls,
            dialog_data_keys=["track_id"],
            when=~F["tiktok_url"] & ~F["youtube_url"],
        ),
        Group(
            StartWithData(
                Const("Изменить исполнителя"),
                id="edit_artist",
                state=AdminTrackEditArtistSG.waiting_for_artist,
                dialog_data_keys=["track_id"],
            ),
            StartWithData(
                Const("Изменить название"),
                id="edit_title",
                state=AdminTrackEditTitleSG.waiting_for_title,
                dialog_data_keys=["track_id"],
            ),
            StartWithData(
                Const("Изменить TikTok"),
                id="edit_tiktok_url",
                state=AdminTrackEditTiktokUrlSG.waiting_for_url,
                dialog_data_keys=["track_id"],
                when=F["tiktok_url"] | F["youtube_url"],
            ),
            StartWithData(
                Const("Изменить YouTube"),
                id="edit_youtube_url",
                state=AdminTrackEditYoutubeUrlSG.waiting_for_url,
                dialog_data_keys=["track_id"],
                when=F["youtube_url"] | F["tiktok_url"],
            ),
            width=2,
        ),
        StartWithData(
            Const("Удалить"),
            id="delete",
            state=AdminTrackDeleteSG.waiting_for_confirmation,
            dialog_data_keys=["track_id"],
        ),
        state=AdminTrackSG.waiting_for_action,
        getter=getters.get_track_data,
        on_process_result=handlers.handle_process_result,
    ),
    on_start=handlers.handle_start,
)

admin_track_release_dialog = Dialog(
    Window(
        Const("Введи ссылку на TikTok, потом YouTube с новой строки"),
        Toggle(
            Format("{item[1]}"),
            id="delay",
            item_id_getter=lambda x: x[0],
            items="delays",
        ),
        Cancel(Const("« Назад")),
        TextInput(
            "urls",
            type_factory=lambda x: x.split("\n"),
            on_success=handlers.handle_release_urls_input,
        ),
        state=AdminTrackReleaseSG.waiting_for_urls,
        getter=getters.get_release_delays,
    ),
)

admin_track_edit_artist_dialog = Dialog(
    Window(
        Const("Введи имя исполнителя"),
        Cancel(Const("« Назад")),
        TextInput(
            "artist",
            on_success=handlers.handle_edit_artist_input,
        ),
        state=AdminTrackEditArtistSG.waiting_for_artist,
    ),
)

admin_track_edit_title_dialog = Dialog(
    Window(
        Const("Введи название"),
        Cancel(Const("« Назад")),
        TextInput(
            "title",
            on_success=handlers.handle_edit_title_input,
        ),
        state=AdminTrackEditTitleSG.waiting_for_title,
    ),
)

admin_track_edit_tiktok_url_dialog = Dialog(
    Window(
        Const("Введи ссылку на TikTok"),
        Cancel(Const("« Назад")),
        TextInput(
            "tiktok_url",
            on_success=handlers.handle_edit_tiktok_url_input,
        ),
        state=AdminTrackEditTiktokUrlSG.waiting_for_url,
    ),
)

admin_track_edit_youtube_url_dialog = Dialog(
    Window(
        Const("Введи ссылку на YouTube"),
        Cancel(Const("« Назад")),
        TextInput(
            "youtube_url",
            on_success=handlers.handle_edit_youtube_url_input,
        ),
        state=AdminTrackEditYoutubeUrlSG.waiting_for_url,
    ),
)


admin_track_delete_dialog = Dialog(
    Window(
        Const("Вы уверены, что хотите удалить трек?"),
        Column(
            Button(
                Const("Да, удалить"),
                id="delete",
                on_click=handlers.handle_delete_confirmation_input,
            ),
            Cancel(Const("« Назад")),
        ),
        state=AdminTrackDeleteSG.waiting_for_confirmation,
    ),
)
