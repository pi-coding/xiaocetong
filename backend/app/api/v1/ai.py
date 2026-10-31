from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_role
from app.core.response import ok
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI 助手"])


class ChatIn(BaseModel):
    message: str = Field(min_length=1, max_length=500)
    scene: Literal["auto", "student", "admin"] = "auto"


class DescribeIn(BaseModel):
    text: str = Field(min_length=2, max_length=500)


@router.post("/chat", summary="AI 助手对话")
def chat(
    payload: ChatIn,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return ok(ai_service.chat(db, user, payload.message, payload.scene))


@router.post("/describe-problem", summary="问题描述润色")
def describe_problem(
    payload: DescribeIn,
    user=Depends(require_role("student")),
):
    return ok(ai_service.describe_problem(payload.text))


@router.get("/insight", summary="运营洞察")
def insight(
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return ok(ai_service.build_insight(db))