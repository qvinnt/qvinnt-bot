from __future__ import annotations

from aiogram import Router


def get_dialogs_router() -> Router:
    from . import admin, example, suggest, top

    router = Router()
    router.include_router(admin.get_dialogs_router())
    router.include_router(example.get_dialogs_router())
    router.include_router(suggest.get_dialogs_router())
    router.include_router(top.get_dialogs_router())

    return router
