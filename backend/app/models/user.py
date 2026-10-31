from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    real_name: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[str] = mapped_column(String(16), default="student", nullable=False, index=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    student_no: Mapped[Optional[str]] = mapped_column(String(32), unique=True, nullable=True)
    building: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    room_no: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    points_balance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    status: Mapped[int] = mapped_column(SmallInteger, default=1, nullable=False)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)