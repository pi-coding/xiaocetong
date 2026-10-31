from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Toilet(Base, TimestampMixin):
    __tablename__ = "toilet"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    type: Mapped[str] = mapped_column(String(16), default="public", nullable=False, index=True)
    building: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    floor: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    location_desc: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    gender: Mapped[str] = mapped_column(String(8), default="all", nullable=False)
    stall_count: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    status: Mapped[str] = mapped_column(String(16), default="normal", nullable=False, index=True)
    cleaner_id: Mapped[Optional[int]] = mapped_column(ForeignKey("staff.id"), nullable=True, index=True)
    clean_interval_min: Mapped[int] = mapped_column(Integer, default=240, nullable=False)
    last_cleaned_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    avg_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("5.00"), nullable=False)
    order_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    qr_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, nullable=True)
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)