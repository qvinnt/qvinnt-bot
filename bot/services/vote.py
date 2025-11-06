from __future__ import annotations

from typing import TYPE_CHECKING

from psycopg.errors import ForeignKeyViolation, UniqueViolation
from sqlalchemy.exc import IntegrityError

from bot.cache.redis import clear_cache
from bot.database.models import VoteModel
from bot.services import errors
from bot.services.track import get_tracks_by_votes

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


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

    return new_vote
