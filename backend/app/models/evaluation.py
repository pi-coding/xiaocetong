from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Evaluation(Base, TimestampMixin):
    __tablename__ = "evaluation"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("service_order.id"), unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    staff_id: Mapped[Optional[int]] = mapped_column(ForeignKey("staff.id"), nullable=True, index=True)
    toilet_id: Mapped[int] = mapped_column(ForeignKey("toilet.id"), nullable=False, index=True)
    score: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    tags: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reply: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reply_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    is_appeal: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)