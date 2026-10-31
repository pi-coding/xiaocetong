from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Integer, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class Staff(Base, TimestampMixin):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user.id"), nullable=True, unique=True)
    staff_no: Mapped[str] = mapped_column(String(32), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    work_type: Mapped[str] = mapped_column(String(16), default="cleaner", nullable=False)
    area: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[str] = mapped_column(String(8), default="on", nullable=False, index=True)
    current_load: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_daily_orders: Mapped[int] = mapped_column(SmallInteger, default=20, nullable=False)
    today_orders: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)
    avg_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("5.00"), nullable=False)
    done_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    avg_duration_min: Mapped[Decimal] = mapped_column(Numeric(6, 1), default=Decimal("0.0"), nullable=False)