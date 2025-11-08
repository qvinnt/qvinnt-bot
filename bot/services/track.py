from __future__ import annotations

from typing import TYPE_CHECKING

from psycopg.errors import UniqueViolation
from sqlalchemy import desc, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from bot.cache.redis import build_key, build_key_with_defaults, cached, clear_cache
from bot.database.models import TrackModel, VoteModel
from bot.services import errors

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@cached(key_builder=build_key_with_defaults("limit", "offset", "ignore_used"))
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
            TrackModel.id.desc(),
        )
    )

    if ignore_used:
        query = query.where(TrackModel.is_used == False)  # noqa: E712

    query = query.limit(limit).offset(offset)

    result = await session.execute(query)
    rows = result.all()

    return [(row[0], row[1] or 0) for row in rows]


@cached(key_builder=build_key_with_defaults("ignore_used"))
async def get_tracks_count(
    session: AsyncSession,
    *,
    ignore_used: bool = True,
) -> int:
    """Get the number of tracks.

    Returns:
        The number of tracks.

    """
    query = select(func.count(TrackModel.id))
    if ignore_used:
        query = query.where(TrackModel.is_used == False)  # noqa: E712

    result = await session.execute(query)
    return result.scalar_one()


async def search_tracks(
    session: AsyncSession,
    query_string: str,
    artist_name: str | None = None,
    limit: int = 3,
    similarity_threshold: float = 0.3,
) -> list[TrackModel]:
    """Search for tracks in the database by title and optionally artist.

    Uses PostgreSQL trigram similarity for fuzzy matching (handles typos).
    Falls back to ILIKE if no similarity matches found.

    Args:
        session: Database session.
        query_string: Track title to search for.
        artist_name: Optional artist name to narrow search.
        limit: Maximum number of results to return.
        similarity_threshold: Minimum similarity score (0-1). Lower = more lenient.

    Returns:
        List of matching TrackModel instances, ordered by similarity score.

    """
    if artist_name:
        # Search by both artist and title with similarity
        query = (
            select(TrackModel)
            .where(
                text(
                    """
                    (similarity(LOWER(artist), LOWER(:artist_name)) > :threshold OR
                     LOWER(artist) LIKE LOWER(:artist_like)) AND
                    (similarity(LOWER(title), LOWER(:query_string)) > :threshold OR
                     LOWER(title) LIKE LOWER(:query_like))
                    """
                )
            )
            .order_by(
                desc(
                    text(
                        """
                        (similarity(LOWER(artist), LOWER(:artist_name)) +
                         similarity(LOWER(title), LOWER(:query_string))) / 2
                        """
                    )
                )
            )
            .params(
                artist_name=artist_name,
                query_string=query_string,
                threshold=similarity_threshold,
                artist_like=f"%{artist_name}%",
                query_like=f"%{query_string}%",
            )
            .limit(limit)
        )
    else:
        # Search by title or artist with similarity
        query = (
            select(TrackModel)
            .where(
                text(
                    """
                    similarity(LOWER(title), LOWER(:query_string)) > :threshold OR
                    similarity(LOWER(artist), LOWER(:query_string)) > :threshold OR
                    LOWER(title) LIKE LOWER(:query_like) OR
                    LOWER(artist) LIKE LOWER(:query_like)
                    """
                )
            )
            .order_by(
                desc(
                    text(
                        """
                        GREATEST(
                            similarity(LOWER(title), LOWER(:query_string)),
                            similarity(LOWER(artist), LOWER(:query_string))
                        )
                        """
                    )
                )
            )
            .params(
                query_string=query_string,
                threshold=similarity_threshold,
                query_like=f"%{query_string}%",
            )
            .limit(limit)
        )

    result = await session.execute(query)
    return list(result.scalars().all())


@cached(key_builder=lambda session, track_id: build_key(track_id))
async def get_track_by_id(
    session: AsyncSession,
    track_id: int,
) -> TrackModel | None:
    return await session.get(TrackModel, track_id)


@cached(key_builder=lambda session, title, artist: build_key(title, artist))
async def get_track_by_title_and_artist(
    session: AsyncSession,
    title: str,
    artist: str,
) -> TrackModel | None:
    query = select(TrackModel).where(
        TrackModel.title == title,
        TrackModel.artist == artist,
    )
    result = await session.execute(query)
    return result.scalar_one_or_none()


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
        await session.rollback()

        if isinstance(e.orig, UniqueViolation):  # pyright: ignore[reportAttributeAccessIssue]
            msg = f"track already exists for artist {artist} and title {title}"
            raise errors.TrackAlreadyExistsError(msg) from e

        raise errors.TrackServiceError(str(e)) from e

    await clear_cache(get_tracks_by_votes)
    await clear_cache(get_tracks_count)
    await clear_cache(get_track_by_id, new_track.id)
    await clear_cache(get_track_by_title_and_artist, title, artist)

    return new_track
