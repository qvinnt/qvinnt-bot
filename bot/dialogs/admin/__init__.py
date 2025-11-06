from __future__ import annotations

from aiogram import Router


def get_dialogs_router() -> Router:
    from . import track

    router = Router()
    router.include_router(track.get_dialogs_router())

    return router
