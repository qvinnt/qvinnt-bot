from __future__ import annotations

from aiogram.fsm.state import State, StatesGroup


class AdminTrackSG(StatesGroup):
    waiting_for_track = State()
    waiting_for_action = State()


class AdminTrackReleaseSG(StatesGroup):
    waiting_for_urls = State()


class AdminTrackEditTitleSG(StatesGroup):
    waiting_for_title = State()


class AdminTrackEditArtistSG(StatesGroup):
    waiting_for_artist = State()


class AdminTrackEditTiktokUrlSG(StatesGroup):
    waiting_for_url = State()


class AdminTrackEditYoutubeUrlSG(StatesGroup):
    waiting_for_url = State()


class AdminTrackDeleteSG(StatesGroup):
    waiting_for_confirmation = State()
