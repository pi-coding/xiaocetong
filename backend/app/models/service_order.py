from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class ServiceOrder(Base, TimestampMixin):
    __tablename__ = "service_order"
    __table_args__ = (
        Index("ix_order_status_created", "status", "created_at"),
        Index("ix_order_user_toilet_status", "user_id", "toilet_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_no: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    toilet_id: Mapped[int] = mapped_column(ForeignKey("toilet.id"), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(64), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(String(8), default="normal", nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="pending", nullable=False, index=True)
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("staff.id"), nullable=True, index=True)
    dispatch_type: Mapped[str] = mapped_column(String(8), default="manual", nullable=False)
    dispatch_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    expect_finish_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    assigned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    accepted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    finish_images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    finish_remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_timeout: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False, index=True)
    rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    urge_count: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    last_urged_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)