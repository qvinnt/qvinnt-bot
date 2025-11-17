from __future__ import annotations

import math
from typing import TYPE_CHECKING

from aiogram_dialog.widgets.text import Text

if TYPE_CHECKING:
    from collections.abc import Callable

    from aiogram_dialog.api.protocols import DialogManager
    from aiogram_dialog.widgets.common import (
        WhenCondition,
    )

    from bot.database.models import TrackModel


class TrackText(Text):
    def __init__(
        self,
        item: str,
        track_getter: Callable[[dict], TrackModel],
        votes_getter: Callable[[dict], int],
        max_length: int = 46,
        votes_emoji: str = "⭐️",
        track_separator: str = " - ",
        votes_separator: str = " | ",
        when: WhenCondition = None,
    ) -> None:
        super().__init__(when=when)
        self.item = item
        self.track_getter = track_getter
        self.votes_getter = votes_getter
        self.max_length = max_length
        self.votes_emoji = votes_emoji
        self.track_separator = track_separator
        self.votes_separator = votes_separator

    async def _render_text(
        self,
        data: dict,
        manager: DialogManager,  # noqa: ARG002
    ) -> str:
        track = self.track_getter(data[self.item])
        votes = self.votes_getter(data[self.item])

        artist = track.artist
        title = track.title

        votes_text = f"{self.votes_separator} {votes} {self.votes_emoji}"

        total_length = len(artist) + len(self.track_separator) + len(title) + len(votes_text)

        if total_length <= self.max_length:
            return artist + self.track_separator + title + votes_text

        if len(artist) == len(title):
            tranc = math.ceil((total_length + 2 - self.max_length) / 2)
            return artist[:-tranc].strip() + "…" + self.track_separator + title[:-tranc].strip() + "…" + votes_text

        if len(artist) > len(title):
            tranc = total_length + 1 - self.max_length
            return artist[:-tranc].strip() + "…" + self.track_separator + title + votes_text

        if len(artist) < len(title):
            tranc = total_length + 1 - self.max_length
            return artist + self.track_separator + title[:-tranc].strip() + "…" + votes_text

        return artist + self.track_separator + title + votes_text
