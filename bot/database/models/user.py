from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import expression

from bot.database.models.base import Base, TimestampMixin, big_int_pk, str_32, str_64, str_255


class UserModel(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[big_int_pk]
    username: Mapped[str_32 | None]
    first_name: Mapped[str_255 | None]
    last_name: Mapped[str_255 | None]
    deep_link: Mapped[str_64 | None]
    has_blocked_bot: Mapped[bool] = mapped_column(server_default=expression.false())

    repr_cols = ("id", "username")
    repr_cols_num = 2

    @property
    def full_name(self) -> str:
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        if self.first_name:
            return self.first_name
        if self.last_name:
            return self.last_name
        if self.username:
            return self.username
        return str(self.id)
