from typing import Literal, Optional

from pydantic import BaseModel, Field

WorkType = Literal["cleaner", "plumber", "all"]
StaffStatus = Literal["on", "off"]


class StaffCreateIn(BaseModel):
    staff_no: str = Field(min_length=2, max_length=32)
    name: str = Field(min_length=1, max_length=50)
    phone: str = Field(min_length=6, max_length=20)
    work_type: WorkType = "cleaner"
    area: Optional[str] = Field(default=None, max_length=64)
    status: StaffStatus = "on"
    max_daily_orders: int = Field(default=20, ge=1, le=100)
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)


class StaffUpdateIn(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=50)
    phone: Optional[str] = Field(default=None, min_length=6, max_length=20)
    work_type: Optional[WorkType] = None
    area: Optional[str] = Field(default=None, max_length=64)
    max_daily_orders: Optional[int] = Field(default=None, ge=1, le=100)


class StaffAdminOut(BaseModel):
    id: int
    staff_no: str
    name: str
    phone: str
    work_type: str
    area: Optional[str] = None
    status: str
    current_load: int
    today_orders: int
    done_count: int
    avg_score: float
    avg_duration_min: float
    max_daily_orders: int
    toilet_count: int = 0
    user_id: Optional[int] = None
    account: Optional[str] = None