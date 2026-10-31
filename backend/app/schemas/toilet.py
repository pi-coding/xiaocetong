from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ToiletType = Literal["public", "dorm"]
ToiletStatus = Literal["normal", "dirty", "fault", "maintenance"]
GenderType = Literal["male", "female", "all"]


class ToiletBaseIn(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    type: ToiletType = "public"
    building: str = Field(min_length=1, max_length=32)
    floor: int = Field(ge=0, le=99)
    location_desc: Optional[str] = Field(default=None, max_length=128)
    gender: GenderType = "all"
    stall_count: int = Field(default=1, ge=1, le=99)
    status: ToiletStatus = "normal"
    cleaner_id: Optional[int] = None
    clean_interval_min: int = Field(default=240, ge=30, le=10080)
    remark: Optional[str] = Field(default=None, max_length=255)


class ToiletCreateIn(ToiletBaseIn):
    code: str = Field(min_length=2, max_length=32, pattern=r"^[A-Za-z0-9\-]+$")


class ToiletUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=64)
    type: Optional[ToiletType] = None
    building: Optional[str] = Field(default=None, min_length=1, max_length=32)
    floor: Optional[int] = Field(default=None, ge=0, le=99)
    location_desc: Optional[str] = Field(default=None, max_length=128)
    gender: Optional[GenderType] = None
    stall_count: Optional[int] = Field(default=None, ge=1, le=99)
    status: Optional[ToiletStatus] = None
    cleaner_id: Optional[int] = None
    clean_interval_min: Optional[int] = Field(default=None, ge=30, le=10080)
    remark: Optional[str] = Field(default=None, max_length=255)


class ToiletOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name: str
    type: str
    building: str
    floor: int
    location_desc: Optional[str] = None
    gender: str
    gender_text: str = ""
    stall_count: int
    status: str
    status_text: str = ""
    cleaner_id: Optional[int] = None
    cleaner_name: Optional[str] = None
    clean_interval_min: int
    last_cleaned_at: Optional[datetime] = None
    avg_score: float
    order_count: int
    qr_token: Optional[str] = None
    remark: Optional[str] = None
    overdue_minutes: int = 0
    warn_level: int = 0
    never_cleaned: bool = False
    active_order_count: int = 0
    bound_count: int = 0
    created_at: Optional[datetime] = None


class ToiletQrOut(BaseModel):
    toilet_id: int
    code: str
    name: str
    token: str
    content: str
