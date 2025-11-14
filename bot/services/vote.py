from __future__ import annotations

from typing import TYPE_CHECKING, Sequence

from psycopg.errors import ForeignKeyViolation, UniqueViolation
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from bot.cache.redis import build_key, cached, clear_cache
from bot.database.models import VoteModel
from bot.services import errors
from bot.services.track import get_tracks_by_votes

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


@cached(key_builder=lambda session, track_id: build_key(track_id))
async def get_votes_count_by_track(
    session: AsyncSession,
    track_id: int,
) -> int:
    query = select(func.count(VoteModel.id)).where(VoteModel.track_id == track_id)
    result = await session.execute(query)
    return result.scalar_one()


async def get_votes_by_track(
    session: AsyncSession,
    track_id: int,
) -> Sequence[VoteModel]:
    query = select(VoteModel).where(VoteModel.track_id == track_id)
    result = await session.execute(query)
    return result.scalars().all()


async def create_vote(
    session: AsyncSession,
    user_id: int,
    track_id: int,
) -> VoteModel:
    """Create a new vote.

    Raises:
        VoteAlreadyExistsError: If vote already exists.
        TrackNotFoundError: If track doesn't exist.
        UserNotFoundError: If user doesn't exist.
        VoteServiceError: If vote creation fails.

    """
    new_vote = VoteModel(
        user_id=user_id,
        track_id=track_id,
    )
    session.add(new_vote)

    try:
        await session.flush()
    except IntegrityError as e:
        await session.rollback()

        if isinstance(e.orig, UniqueViolation):
            msg = f"vote already exists for user {user_id} and track {track_id}"
            raise errors.VoteAlreadyExistsError(msg) from e

        if isinstance(e.orig, ForeignKeyViolation):
            match e.orig.diag.table_name:
                case "tracks":
                    msg = f"track {track_id} not found"
                    raise errors.TrackNotFoundError(msg) from e
                case "users":
                    msg = f"user {user_id} not found"
                    raise errors.UserNotFoundError(msg) from e

        raise errors.VoteServiceError(str(e)) from e

    await clear_cache(get_tracks_by_votes)
    await clear_cache(get_votes_count_by_track, track_id)

    return new_vote
