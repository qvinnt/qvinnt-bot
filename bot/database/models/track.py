from sqlalchemy import UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression

from bot.database.models.base import Base, TimestampMixin, int_pk, str_255


class TrackModel(TimestampMixin, Base):
    __tablename__ = "tracks"

    id: Mapped[int_pk]
    artist: Mapped[str_255]
    title: Mapped[str_255]
    tiktok_url: Mapped[str_255 | None] = mapped_column(server_default=expression.null())
    youtube_url: Mapped[str_255 | None] = mapped_column(server_default=expression.null())

    repr_cols = ("id", "title", "artist")
    repr_cols_num = 3

    __table_args__ = (
        UniqueConstraint(
            "artist",
            "title",
        ),
    )
