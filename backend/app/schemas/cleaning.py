from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field

CleanType = Literal["routine", "order", "emergency"]
CleanResult = Literal["pass", "fail"]


class CleaningCreateIn(BaseModel):
    toilet_id: int
    staff_id: Optional[int] = None
    order_id: Optional[int] = None
    clean_type: CleanType = "routine"
    clean_items: list[str] = Field(default_factory=list, max_length=10)
    before_images: list[str] = Field(default_factory=list, max_length=3)
    after_images: list[str] = Field(default_factory=list, max_length=3)
    duration_min: Optional[int] = Field(default=None, ge=0, le=600)
    result: CleanResult = "pass"
    remark: Optional[str] = Field(default=None, max_length=255)


class CleaningLogOut(BaseModel):
    id: int
    toilet_id: int
    toilet_name: Optional[str] = None
    toilet_code: Optional[str] = None
    building: Optional[str] = None
    floor: Optional[int] = None
    staff_id: int
    staff_name: Optional[str] = None
    order_id: Optional[int] = None
    clean_type: str
    clean_type_text: str = ""
    clean_items: list[str] = Field(default_factory=list)
    before_images: list[str] = Field(default_factory=list)
    after_images: list[str] = Field(default_factory=list)
    duration_min: Optional[int] = None
    result: str
    remark: Optional[str] = None
    cleaned_at: Optional[datetime] = None
    created_at: Optional[datetime] = None