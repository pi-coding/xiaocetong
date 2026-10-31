from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.core.response import BizCode
from app.models import Evaluation, ServiceOrder, Staff, Toilet, User
from app.schemas.evaluation import EvaluationCreateIn
from app.services import points_service

EVALUATE_POINTS = 5


def _round2(value) -> Decimal:
    return Decimal(str(round(float(value or 0), 2)))


def recompute_toilet_score(db: Session, toilet_id: int) -> None:
    avg = db.scalar(select(func.avg(Evaluation.score)).where(Evaluation.toilet_id == toilet_id))
    toilet = db.get(Toilet, toilet_id)
    if toilet is not None:
        toilet.avg_score = _round2(avg) if avg is not None else Decimal("5.00")


def recompute_staff_score(db: Session, staff_id: int) -> None:
    avg = db.scalar(select(func.avg(Evaluation.score)).where(Evaluation.staff_id == staff_id))
    staff = db.get(Staff, staff_id)
    if staff is not None:
        staff.avg_score = _round2(avg) if avg is not None else Decimal("5.00")


def create_evaluation(db: Session, order_id: int, user: User, payload: EvaluationCreateIn) -> Evaluation:
    order = db.get(ServiceOrder, order_id)
    if order is None:
        raise BizException(BizCode.NOT_FOUND, "工单不存在")
    if order.user_id != user.id:
        raise BizException(BizCode.FORBIDDEN, "只能评价自己的工单")
    if order.status != "done":
        raise BizException(BizCode.STATE_ERROR, "工单尚未完成，暂不能评价")
    existing = db.scalar(select(Evaluation).where(Evaluation.order_id == order.id))
    if existing is not None:
        raise BizException(BizCode.DUPLICATE, "该工单已评价")

    evaluation = Evaluation(
        order_id=order.id,
        user_id=user.id,
        staff_id=order.assignee_id,
        toilet_id=order.toilet_id,
        score=payload.score,
        tags=",".join(payload.tags) if payload.tags else None,
        content=(payload.content or "").strip() or None,
    )
    db.add(evaluation)
    db.flush()

    order.rating = payload.score
    recompute_toilet_score(db, order.toilet_id)
    if order.assignee_id:
        recompute_staff_score(db, order.assignee_id)
    points_service.add_points(
        db,
        user,
        EVALUATE_POINTS,
        "evaluate",
        "evaluation",
        evaluation.id,
        f"评价工单 {order.order_no}",
    )
    db.flush()
    return evaluation


def list_evaluations(
    db: Session,
    score: Optional[int] = None,
    toilet_id: Optional[int] = None,
    staff_id: Optional[int] = None,
    only_appeal: bool = False,
    page: int = 1,
    size: int = 10,
) -> tuple[list[Evaluation], int]:
    stmt = select(Evaluation)
    if score:
        stmt = stmt.where(Evaluation.score == score)
    if toilet_id:
        stmt = stmt.where(Evaluation.toilet_id == toilet_id)
    if staff_id:
        stmt = stmt.where(Evaluation.staff_id == staff_id)
    if only_appeal:
        stmt = stmt.where(Evaluation.is_appeal == 1)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Evaluation.created_at.desc(), Evaluation.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return list(rows), total


def to_dicts(db: Session, evaluations: list[Evaluation]) -> list[dict]:
    if not evaluations:
        return []
    order_ids = {item.order_id for item in evaluations}
    staff_ids = {item.staff_id for item in evaluations if item.staff_id}
    toilet_ids = {item.toilet_id for item in evaluations}
    user_ids = {item.user_id for item in evaluations}

    orders = {item.id: item for item in db.scalars(select(ServiceOrder).where(ServiceOrder.id.in_(order_ids))).all()}
    staffs = {item.id: item for item in db.scalars(select(Staff).where(Staff.id.in_(staff_ids))).all()} if staff_ids else {}
    toilets = {item.id: item for item in db.scalars(select(Toilet).where(Toilet.id.in_(toilet_ids))).all()}
    users = {item.id: item for item in db.scalars(select(User).where(User.id.in_(user_ids))).all()}

    results = []
    for item in evaluations:
        order = orders.get(item.order_id)
        staff = staffs.get(item.staff_id)
        toilet = toilets.get(item.toilet_id)
        user = users.get(item.user_id)
        results.append(
            {
                "id": item.id,
                "order_id": item.order_id,
                "order_no": order.order_no if order else None,
                "user_id": item.user_id,
                "user_name": user.real_name if user else None,
                "staff_id": item.staff_id,
                "staff_name": staff.name if staff else None,
                "toilet_id": item.toilet_id,
                "toilet_name": toilet.name if toilet else None,
                "building": toilet.building if toilet else None,
                "score": item.score,
                "tags": [tag for tag in (item.tags or "").split(",") if tag],
                "content": item.content,
                "reply": item.reply,
                "reply_at": item.reply_at,
                "is_appeal": item.is_appeal,
                "created_at": item.created_at,
            }
        )
    return results