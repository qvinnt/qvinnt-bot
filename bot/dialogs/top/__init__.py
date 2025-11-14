from __future__ import annotations

from aiogram import Router


def get_dialogs_router() -> Router:
    from .dialogs import top_dialog

    router = Router()
    router.include_router(top_dialog)

    return router
