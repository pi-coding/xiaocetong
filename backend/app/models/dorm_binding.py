from sqlalchemy import ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class DormBinding(Base, TimestampMixin):
    __tablename__ = "dorm_binding"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    toilet_id: Mapped[int] = mapped_column(ForeignKey("toilet.id"), nullable=False, index=True)
    building: Mapped[str] = mapped_column(String(32), nullable=False)
    floor: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    room_no: Mapped[str] = mapped_column(String(16), nullable=False)
    bind_type: Mapped[str] = mapped_column(String(16), default="owner", nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False, index=True)