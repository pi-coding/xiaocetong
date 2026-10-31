from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RegisterIn(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=6, max_length=32)
    real_name: str = Field(min_length=1, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=20)
    student_no: Optional[str] = Field(default=None, max_length=32)
    building: Optional[str] = Field(default=None, max_length=32)
    room_no: Optional[str] = Field(default=None, max_length=16)


class LoginIn(BaseModel):
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=1, max_length=32)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    real_name: str
    role: str
    phone: Optional[str] = None
    student_no: Optional[str] = None
    building: Optional[str] = None
    room_no: Optional[str] = None
    avatar: Optional[str] = None
    points_balance: int
    status: int
    last_login_at: Optional[datetime] = None
    created_at: datetime


class TokenOut(BaseModel):
    token: str
    token_type: str = "Bearer"
    expires_in: int
    user: UserOut


class ProfileUpdateIn(BaseModel):
    real_name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    phone: Optional[str] = Field(default=None, max_length=20)
    building: Optional[str] = Field(default=None, max_length=32)
    room_no: Optional[str] = Field(default=None, max_length=16)
    avatar: Optional[str] = Field(default=None, max_length=255)


class PasswordChangeIn(BaseModel):
    old_password: str = Field(min_length=1, max_length=32)
    new_password: str = Field(min_length=6, max_length=32)