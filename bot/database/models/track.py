from typing import Any

from sqlalchemy import UniqueConstraint, case, or_
from sqlalchemy.ext.hybrid import hybrid_property
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

    @hybrid_property
    def is_used(self) -> bool:  # type: ignore[reportRede laration]
        return self.tiktok_url is not None or self.youtube_url is not None

    @is_used.expression
    def is_used(cls) -> expression.Case[Any]:  # noqa: N805
        return case(
            (or_(cls.tiktok_url != None, cls.youtube_url != None), True),  # type: ignore[reportArgumentType]  # noqa: E711
            else_=False,
        )
