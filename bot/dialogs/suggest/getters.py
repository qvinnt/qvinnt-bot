from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aiogram_dialog import DialogManager


async def get_tracks_data(
    dialog_manager: DialogManager,
    **_: Any,
) -> dict[str, ...]:
    tracks = dialog_manager.dialog_data["tracks"]

    return {
        "tracks": list(enumerate(tracks)),
    }
