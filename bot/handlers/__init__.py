from __future__ import annotations

from aiogram import Router


def get_handlers_router() -> Router:
    from . import admin, error, start, suggest, top, user_block

    router = Router(name=__name__)
    router.include_router(error.router)
    router.include_router(user_block.router)
    router.include_router(admin.get_handlers_router())
    router.include_router(start.router)
    router.include_router(suggest.router)
    router.include_router(top.router)

    return router
