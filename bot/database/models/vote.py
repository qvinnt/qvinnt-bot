from sqlalchemy import BigInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.schema import ForeignKey

from bot.database.models.base import Base, TimestampMixin, int_pk


class VoteModel(TimestampMixin, Base):
    __tablename__ = "votes"

    id: Mapped[int_pk]
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(
            "users.id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    )
    track_id: Mapped[int] = mapped_column(
        ForeignKey(
            "tracks.id",
            onupdate="CASCADE",
            ondelete="CASCADE",
        ),
    )

    repr_cols = ("id", "user_id", "track_id")
    repr_cols_num = 3

    __table_args__ = (
        UniqueConstraint(
            user_id,
            track_id,
        ),
    )
