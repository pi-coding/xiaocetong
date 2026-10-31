from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.toilet import ToiletOut

BindType = Literal["owner", "shared"]


class BindingCreateIn(BaseModel):
    building: str = Field(min_length=1, max_length=32)
    room_no: str = Field(min_length=1, max_length=16)
    floor: Optional[int] = Field(default=None, ge=0, le=99)
    bind_type: BindType = "owner"


class BindingUpdateIn(BindingCreateIn):
    pass


class BindingOut(BaseModel):
    id: int
    user_id: int
    toilet_id: int
    building: str
    floor: int
    room_no: str
    bind_type: str
    status: int
    toilet: Optional[ToiletOut] = None


class BindingMatchOut(BaseModel):
    code: str
    exists: bool
    toilet: Optional[ToiletOut] = None