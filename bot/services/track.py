from __future__ import annotations

from typing import TYPE_CHECKING

from psycopg import IntegrityError
from psycopg.errors import UniqueViolation
from sqlalchemy import func, select

from bot.cache.redis import build_key, cached, clear_cache
from bot.database.models import TrackModel, VoteModel
from bot.services import errors

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@cached(key_builder=lambda session, limit, offset, ignore_used: build_key(limit, offset, ignore_used))
async def get_tracks_by_votes(
    session: AsyncSession,
    limit: int = 10,
    offset: int = 0,
    *,
    ignore_used: bool = True,
) -> list[tuple[TrackModel, int]]:
    """Get top n tracks by votes.

    Returns:
        List of tuples containing (TrackModel, vote_count).
        Vote count is 0 for tracks with no votes.

    """
    vote_counts = (
        select(
            VoteModel.track_id,
            func.count(VoteModel.id).label("vote_count"),
        )
        .group_by(VoteModel.track_id)
        .subquery()
    )

    query = (
        select(TrackModel, vote_counts.c.vote_count)
        .outerjoin(vote_counts, TrackModel.id == vote_counts.c.track_id)
        .order_by(
            vote_counts.c.vote_count.desc().nulls_last(),
            TrackModel.id.asc(),
        )
    )

    if ignore_used:
        query = query.where(TrackModel.is_used == False)  # noqa: E712

    query = query.limit(limit).offset(offset)

    result = await session.execute(query)
    rows = result.all()

    return [(row[0], row[1] or 0) for row in rows]


async def create_track(
    session: AsyncSession,
    title: str,
    artist: str,
) -> TrackModel:
    """Create a new track.

    Raises:
        TrackAlreadyExistsError: If track already exists.
        TrackServiceError: If track creation fails.

    """
    new_track = TrackModel(
        title=title,
        artist=artist,
    )

    session.add(new_track)

    try:
        await session.flush()
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):
            msg = f"track already exists for artist {artist} and title {title}"
            raise errors.TrackAlreadyExistsError(msg) from e

        raise errors.TrackServiceError(str(e)) from e

    await clear_cache(get_tracks_by_votes)

    return new_track
