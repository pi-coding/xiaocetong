from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class PointsAdjustIn(BaseModel):
    user_id: int
    amount: int = Field(ge=-10000, le=10000)
    remark: Optional[str] = Field(default=None, max_length=128)


class PointsRecordOut(BaseModel):
    id: int
    amount: int
    balance_after: int
    source: str
    source_text: str = ""
    ref_type: Optional[str] = None
    ref_id: Optional[int] = None
    remark: Optional[str] = None
    created_at: Optional[datetime] = None


class PointsRankItem(BaseModel):
    rank: int
    user_id: int
    name: str
    building: Optional[str] = None
    points_balance: int


class StaffProfileOut(BaseModel):
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
    toilet_count: int = 0