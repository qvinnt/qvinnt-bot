from __future__ import annotations

from aiogram import Router

from bot.filters.admin import AdminFilter


def get_handlers_router() -> Router:
    from . import track

    router = Router(name=__name__)
    router.message.filter(AdminFilter())
    router.include_router(track.router)

    return router
