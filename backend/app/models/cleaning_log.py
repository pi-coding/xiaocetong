from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class CleaningLog(Base, TimestampMixin):
    __tablename__ = "cleaning_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    toilet_id: Mapped[int] = mapped_column(ForeignKey("toilet.id"), nullable=False, index=True)
    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False, index=True)
    order_id: Mapped[Optional[int]] = mapped_column(ForeignKey("service_order.id"), nullable=True, index=True)
    clean_type: Mapped[str] = mapped_column(String(16), default="routine", nullable=False)
    before_images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    after_images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    clean_items: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    duration_min: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    result: Mapped[str] = mapped_column(String(8), default="pass", nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    cleaned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, nullable=False, index=True)