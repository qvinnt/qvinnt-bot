from __future__ import annotations

from aiogram import Router


def get_dialogs_router() -> Router:
    from .dialogs import (
        admin_track_delete_dialog,
        admin_track_dialog,
        admin_track_edit_artist_dialog,
        admin_track_edit_tiktok_url_dialog,
        admin_track_edit_title_dialog,
        admin_track_edit_youtube_url_dialog,
        admin_track_release_dialog,
    )

    router = Router()
    router.include_router(admin_track_dialog)
    router.include_router(admin_track_release_dialog)
    router.include_router(admin_track_edit_artist_dialog)
    router.include_router(admin_track_edit_title_dialog)
    router.include_router(admin_track_edit_tiktok_url_dialog)
    router.include_router(admin_track_edit_youtube_url_dialog)
    router.include_router(admin_track_delete_dialog)

    return router
