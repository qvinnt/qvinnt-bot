from __future__ import annotations

from aiogram import Router


def get_dialogs_router() -> Router:
    from .dialogs import suggest_dialog

    router = Router()
    router.include_router(suggest_dialog)

    return router
