from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

OrderType = Literal["unclog", "clean", "repair"]
OrderPriority = Literal["low", "normal", "high", "urgent"]


class OrderCreateIn(BaseModel):
    toilet_id: int
    type: OrderType
    title: str = Field(min_length=1, max_length=64)
    description: Optional[str] = Field(default=None, max_length=1000)
    images: list[str] = Field(default_factory=list, max_length=6)
    priority: OrderPriority = "normal"


class OrderAssignIn(BaseModel):
    staff_id: int
    from_ai: bool = False
    dispatch_score: Optional[float] = Field(default=None, ge=0, le=100)


class OrderFinishIn(BaseModel):
    finish_images: list[str] = Field(default_factory=list, max_length=6)
    finish_remark: Optional[str] = Field(default=None, max_length=255)


class OrderCloseIn(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=255)


class DispatchRunIn(BaseModel):
    order_ids: list[int] = Field(default_factory=list, max_length=50)


class TimeNode(BaseModel):
    key: str
    title: str
    time: Optional[datetime] = None
    desc: Optional[str] = None


class OrderOut(BaseModel):
    id: int
    order_no: str
    type: str
    type_text: str
    title: str
    description: Optional[str] = None
    images: list[str] = Field(default_factory=list)
    priority: str
    priority_text: str
    status: str
    status_text: str
    toilet_id: int
    toilet_code: Optional[str] = None
    toilet_name: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[int] = None
    location_desc: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    user_phone: Optional[str] = None
    assignee_id: Optional[int] = None
    assignee_name: Optional[str] = None
    assignee_phone: Optional[str] = None
    dispatch_type: str = "manual"
    dispatch_score: Optional[float] = None
    expect_finish_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    assigned_at: Optional[datetime] = None
    accepted_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    finish_images: list[str] = Field(default_factory=list)
    finish_remark: Optional[str] = None
    is_timeout: int = 0
    urge_count: int = 0
    rating: Optional[int] = None
    can_cancel: bool = False
    can_urge: bool = False
    can_evaluate: bool = False


class OrderDetailOut(OrderOut):
    timeline: list[TimeNode] = Field(default_factory=list)


class StaffOptionOut(BaseModel):
    id: int
    staff_no: str
    name: str
    phone: Optional[str] = None
    work_type: str
    area: Optional[str] = None
    status: str
    current_load: int
    max_daily_orders: int
    avg_score: float