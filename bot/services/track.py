from __future__ import annotations

from typing import TYPE_CHECKING

from psycopg.errors import UniqueViolation
from sqlalchemy import desc, exists, func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text

from bot.cache.redis import DAY, build_key, build_key_with_defaults, cached, clear_cache
from bot.database.models import TrackModel, VoteModel
from bot.services import errors

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@cached(ttl=DAY, key_builder=lambda session, track_id: build_key(track_id))
async def track_exists(
    session: AsyncSession,
    track_id: int,
) -> bool:
    query = select(exists().where(TrackModel.id == track_id))
    result = await session.scalar(query)
    return bool(result)


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


async def search_tracks_by_query(
    session: AsyncSession,
    track_query: str,
    limit: int = 3,
    similarity_threshold: float = 0.3,
) -> list[TrackModel]:
    # Parse input - try multiple formats
    artist_name = None
    song_name = track_query

    # Try parsing "Artist - Song" format
    if "-" in track_query:
        parts = track_query.split("-", 1)  # Split only on first "-"
        if len(parts) == 2 and parts[0].strip() and parts[1].strip():  # noqa: PLR2004
            artist_name = parts[0].strip()
            song_name = parts[1].strip()

    # First, search in database with parsed format
    db_tracks = await search_tracks(
        session,
        query_string=song_name,
        artist_name=artist_name,
        limit=limit,
        similarity_threshold=similarity_threshold,
    )

    if not db_tracks and artist_name and song_name:
        db_tracks = await search_tracks(
            session,
            query_string=artist_name,
            artist_name=song_name,
            limit=limit,
            similarity_threshold=similarity_threshold,
        )

    # If no artist was specified and no results found, try splitting on common patterns
    # This handles "Artist Song" format (without "-")
    if artist_name is None and not db_tracks and " " in track_query:
        # Try treating first word(s) as artist, rest as song
        words = track_query.split()
        if len(words) >= 2:  # noqa: PLR2004
            # Try first word as artist
            db_tracks = await search_tracks(
                session,
                query_string=" ".join(words[1:]),
                artist_name=words[0],
                limit=limit,
                similarity_threshold=similarity_threshold,
            )

            # If still no results, try first two words as artist (for multi-word artists)
            if not db_tracks and len(words) >= 3:  # noqa: PLR2004
                db_tracks = await search_tracks(
                    session,
                    query_string=" ".join(words[2:]),
                    artist_name=" ".join(words[:2]),
                    limit=limit,
                    similarity_threshold=similarity_threshold,
                )

    return db_tracks


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

    await clear_cache(track_exists, new_track.id)
    await clear_cache(get_tracks_by_votes)
    await clear_cache(get_tracks_count)
    await clear_cache(get_track_by_id, new_track.id)
    await clear_cache(get_track_by_title_and_artist, title, artist)

    return new_track


async def update_track_title(
    session: AsyncSession,
    track_id: int,
    title: str,
) -> None:
    """Update the title of a track.

    Raises:
        TrackNotFoundError: If track not found.
        TrackAlreadyExistsError: If track already exists.
        TrackServiceError: If track update fails.

    """
    track = await get_track_by_id(session, track_id)

    if not track:
        msg = f"Track with id {track_id} not found"
        raise errors.TrackNotFoundError(msg)

    old_title = track.title

    try:
        await session.execute(update(TrackModel).where(TrackModel.id == track_id).values(title=title))
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):  # pyright: ignore[reportAttributeAccessIssue]
            msg = f"track already exists for artist {track.artist} and title {title}"
            raise errors.TrackAlreadyExistsError(msg) from e

        raise errors.TrackServiceError(str(e)) from e

    await clear_cache(get_track_by_id, track_id)
    await clear_cache(get_tracks_by_votes)
    await clear_cache(get_track_by_title_and_artist, old_title, track.artist)
    await clear_cache(get_track_by_title_and_artist, title, track.artist)


async def update_track_artist(
    session: AsyncSession,
    track_id: int,
    artist: str,
) -> None:
    """Update the artist of a track.

    Raises:
        TrackNotFoundError: If track not found.
        TrackAlreadyExistsError: If track already exists.
        TrackServiceError: If track update fails.

    """
    track = await get_track_by_id(session, track_id)

    if not track:
        msg = f"Track with id {track_id} not found"
        raise errors.TrackNotFoundError(msg)

    old_artist = track.artist

    try:
        await session.execute(update(TrackModel).where(TrackModel.id == track_id).values(artist=artist))
    except IntegrityError as e:
        if isinstance(e.orig, UniqueViolation):  # pyright: ignore[reportAttributeAccessIssue]
            msg = f"track already exists for artist {artist} and title {track.title}"
            raise errors.TrackAlreadyExistsError(msg) from e

        raise errors.TrackServiceError(str(e)) from e

    await clear_cache(get_track_by_id, track_id)
    await clear_cache(get_tracks_by_votes)
    await clear_cache(get_track_by_title_and_artist, track.title, old_artist)
    await clear_cache(get_track_by_title_and_artist, track.title, artist)


async def update_track_tiktok_url(
    session: AsyncSession,
    track_id: int,
    tiktok_url: str | None,
) -> None:
    """Update the TikTok URL of a track.

    Raises:
        TrackNotFoundError: If track not found.

    """
    track = await get_track_by_id(session, track_id)

    if not track:
        msg = f"Track with id {track_id} not found"
        raise errors.TrackNotFoundError(msg)

    await session.execute(update(TrackModel).where(TrackModel.id == track_id).values(tiktok_url=tiktok_url))

    await clear_cache(get_track_by_id, track_id)
    await clear_cache(get_track_by_title_and_artist, track.title, track.artist)
    await clear_cache(get_tracks_by_votes)
    await clear_cache(get_tracks_count)


async def update_track_youtube_url(
    session: AsyncSession,
    track_id: int,
    youtube_url: str | None,
) -> None:
    """Update the YouTube URL of a track.

    Raises:
        TrackNotFoundError: If track not found.
        TrackServiceError: If track update fails.

    """
    track = await get_track_by_id(session, track_id)

    if not track:
        msg = f"Track with id {track_id} not found"
        raise errors.TrackNotFoundError(msg)

    await session.execute(update(TrackModel).where(TrackModel.id == track_id).values(youtube_url=youtube_url))

    await clear_cache(get_track_by_id, track_id)
    await clear_cache(get_track_by_title_and_artist, track.title, track.artist)
    await clear_cache(get_tracks_by_votes)
    await clear_cache(get_tracks_count)


async def delete_track(
    session: AsyncSession,
    track_id: int,
) -> None:
    """Delete a track.

    Raises:
        TrackNotFoundError: If track not found.
        TrackServiceError: If track deletion fails.

    """
    track = await get_track_by_id(session, track_id)

    if not track:
        msg = f"Track with id {track_id} not found"
        raise errors.TrackNotFoundError(msg)

    await session.delete(track)

    from bot.services.vote import get_votes_count_by_track

    await clear_cache(track_exists, track_id)
    await clear_cache(get_track_by_id, track_id)
    await clear_cache(get_track_by_title_and_artist, track.title, track.artist)
    await clear_cache(get_tracks_by_votes)
    await clear_cache(get_tracks_count)
    await clear_cache(get_votes_count_by_track, track_id)
