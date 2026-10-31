from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.core.exceptions import BizException
from app.core.response import BizCode, ok, page_data
from app.models import Evaluation
from app.schemas.evaluation import EvaluationCreateIn, EvaluationOut, EvaluationReplyIn
from app.services import evaluation_service, points_service

router = APIRouter(tags=["评价"])


@router.post("/orders/{order_id}/evaluation", summary="提交工单评价")
def create_evaluation(
    order_id: int,
    payload: EvaluationCreateIn,
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    evaluation = evaluation_service.create_evaluation(db, order_id, user, payload)
    db.commit()
    db.refresh(evaluation)
    data = evaluation_service.to_dicts(db, [evaluation])[0]
    return ok(EvaluationOut(**data).model_dump(mode="json"), "评价成功，积分 +5")


@router.get("/evaluations", summary="评价列表（管理端）")
def list_evaluations(
    score: Optional[int] = Query(default=None, ge=1, le=5),
    toilet_id: Optional[int] = Query(default=None, ge=1),
    staff_id: Optional[int] = Query(default=None, ge=1),
    only_appeal: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    rows, total = evaluation_service.list_evaluations(
        db, score, toilet_id, staff_id, only_appeal, page, size
    )
    items = [EvaluationOut(**item).model_dump(mode="json") for item in evaluation_service.to_dicts(db, rows)]
    return ok(page_data(items, total, page, size))


@router.get("/evaluations/my", summary="我的评价")
def my_evaluations(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    total = db.scalar(select(func.count(Evaluation.id)).where(Evaluation.user_id == user.id)) or 0
    rows = db.scalars(
        select(Evaluation)
        .where(Evaluation.user_id == user.id)
        .order_by(Evaluation.created_at.desc(), Evaluation.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    items = [EvaluationOut(**item).model_dump(mode="json") for item in evaluation_service.to_dicts(db, list(rows))]
    return ok(page_data(items, total, page, size))


@router.put("/evaluations/{evaluation_id}/reply", summary="回复评价")
def reply_evaluation(
    evaluation_id: int,
    payload: EvaluationReplyIn,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    evaluation = db.get(Evaluation, evaluation_id)
    if evaluation is None:
        raise BizException(BizCode.NOT_FOUND, "评价不存在")
    evaluation.reply = payload.reply.strip()
    evaluation.reply_at = datetime.now()
    db.commit()
    db.refresh(evaluation)
    return ok(EvaluationOut(**evaluation_service.to_dicts(db, [evaluation])[0]).model_dump(mode="json"), "回复成功")


@router.put("/evaluations/{evaluation_id}/appeal", summary="标记评价申诉")
def appeal_evaluation(
    evaluation_id: int,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    evaluation = db.get(Evaluation, evaluation_id)
    if evaluation is None:
        raise BizException(BizCode.NOT_FOUND, "评价不存在")
    evaluation.is_appeal = 0 if evaluation.is_appeal else 1
    db.commit()
    db.refresh(evaluation)
    return ok(EvaluationOut(**evaluation_service.to_dicts(db, [evaluation])[0]).model_dump(mode="json"), "申诉标记已更新")