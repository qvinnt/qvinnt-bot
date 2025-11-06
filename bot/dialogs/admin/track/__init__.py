from __future__ import annotations

from aiogram import Router


def get_dialogs_router() -> Router:
    # from .dialogs import admin_track_dialog

    router = Router()
    # router.include_router(admin_track_dialog)

    return router
