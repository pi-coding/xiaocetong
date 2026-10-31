from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    list: list
    total: int
    page: int
    size: int
    pages: int


class SimpleOut(BaseModel):
    id: int
    name: str


class TimeRangeIn(BaseModel):
    start: Optional[datetime] = None
    end: Optional[datetime] = None


class IdsIn(BaseModel):
    ids: list[int] = Field(default_factory=list, min_length=1)