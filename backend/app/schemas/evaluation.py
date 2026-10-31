from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class EvaluationCreateIn(BaseModel):
    score: int = Field(ge=1, le=5)
    tags: list[str] = Field(default_factory=list, max_length=6)
    content: Optional[str] = Field(default=None, max_length=500)


class EvaluationReplyIn(BaseModel):
    reply: str = Field(min_length=1, max_length=500)


class EvaluationOut(BaseModel):
    id: int
    order_id: int
    order_no: Optional[str] = None
    user_id: int
    user_name: Optional[str] = None
    staff_id: Optional[int] = None
    staff_name: Optional[str] = None
    toilet_id: int
    toilet_name: Optional[str] = None
    building: Optional[str] = None
    score: int
    tags: list[str] = Field(default_factory=list)
    content: Optional[str] = None
    reply: Optional[str] = None
    reply_at: Optional[datetime] = None
    is_appeal: int = 0
    created_at: Optional[datetime] = None