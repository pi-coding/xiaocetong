from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.models import ServiceOrder, Staff, Toilet
from app.services import order_service

WEIGHTS = {"idle": 0.35, "speed": 0.25, "rating": 0.20, "area": 0.20}

LOAD_CAPACITY = 5
SPEED_FAST_MIN = 30
SPEED_SLOW_MIN = 240


def _idle_score(staff: Staff) -> float:
    return max(0.0, 1 - staff.current_load / LOAD_CAPACITY)


def _speed_score(staff: Staff) -> float:
    if not staff.done_count:
        return 0.65
    duration = float(staff.avg_duration_min or 0)
    if duration <= SPEED_FAST_MIN:
        return 1.0
    if duration >= SPEED_SLOW_MIN:
        return 0.0
    return 1 - (duration - SPEED_FAST_MIN) / (SPEED_SLOW_MIN - SPEED_FAST_MIN)


def _rating_score(staff: Staff) -> float:
    return max(0.0, min(1.0, float(staff.avg_score or 0) / 5))


def _area_score(staff: Staff, building: Optional[str]) -> float:
    if not building:
        return 0.6
    area = staff.area or ""
    return 1.0 if building in area else 0.15


def score_candidate(order: ServiceOrder, toilet: Optional[Toilet], staff: Staff) -> dict:
    idle = _idle_score(staff)
    speed = _speed_score(staff)
    rating = _rating_score(staff)
    area = _area_score(staff, toilet.building if toilet else None)
    total = 100 * (
        WEIGHTS["idle"] * idle
        + WEIGHTS["speed"] * speed
        + WEIGHTS["rating"] * rating
        + WEIGHTS["area"] * area
    )

    reasons = []
    if toilet and area >= 1.0:
        reasons.append(f"负责 {toilet.building} 栋，区域匹配")
    elif toilet:
        reasons.append(f"非 {toilet.building} 栋责任区，跨区支援")
    reasons.append(f"当前在途 {staff.current_load} 单，接单压力{'小' if idle >= 0.6 else '较大'}")
    if staff.done_count:
        reasons.append(f"平均处理 {float(staff.avg_duration_min):.0f} 分钟，评分 {float(staff.avg_score):.1f}")
    else:
        reasons.append("暂无历史工单，按中性时效估算")

    return {
        "staff_id": staff.id,
        "staff_no": staff.staff_no,
        "name": staff.name,
        "phone": staff.phone,
        "work_type": staff.work_type,
        "area": staff.area,
        "current_load": staff.current_load,
        "avg_score": float(staff.avg_score or 0),
        "avg_duration_min": float(staff.avg_duration_min or 0),
        "done_count": staff.done_count,
        "score": round(total, 1),
        "factors": {
            "idle": round(idle * 100, 1),
            "speed": round(speed * 100, 1),
            "rating": round(rating * 100, 1),
            "area": round(area * 100, 1),
        },
        "reasons": reasons,
    }


def candidates_for_order(db: Session, order: ServiceOrder, limit: int = 3) -> list[dict]:
    toilet = db.get(Toilet, order.toilet_id)
    staffs = db.scalars(select(Staff).where(Staff.status == "on")).all()
    results = []
    for staff in staffs:
        if not order_service.can_dispatch_staff(staff, order.type):
            continue
        if order_service.today_assigned_count(db, staff.id) >= staff.max_daily_orders:
            continue
        if order.status == "assigned" and order.assignee_id == staff.id:
            continue
        results.append(score_candidate(order, toilet, staff))
    results.sort(key=lambda item: item["score"], reverse=True)
    return results[:limit]


def suggest_for_order(db: Session, order: ServiceOrder, limit: int = 3) -> dict:
    detail = order_service.to_dicts(db, [order])[0]
    return {
        "order": detail,
        "candidates": candidates_for_order(db, order, limit),
        "weights": WEIGHTS,
        "generated_at": datetime.now(),
    }


def suggest_all(db: Session, limit: int = 3, max_orders: int = 20) -> list[dict]:
    orders = db.scalars(
        select(ServiceOrder)
        .where(ServiceOrder.status == "pending")
        .order_by(ServiceOrder.created_at.asc())
        .limit(max_orders)
    ).all()
    return [suggest_for_order(db, order, limit) for order in orders]


def run_ai_dispatch(db: Session, order_ids: Optional[list[int]] = None) -> dict:
    stmt = select(ServiceOrder).where(ServiceOrder.status == "pending")
    if order_ids:
        stmt = stmt.where(ServiceOrder.id.in_(order_ids))
    orders = db.scalars(stmt.order_by(ServiceOrder.created_at.asc())).all()

    dispatched = []
    failed = []
    for order in orders:
        candidates = candidates_for_order(db, order, 1)
        if not candidates:
            failed.append({"order_id": order.id, "order_no": order.order_no, "reason": "暂无可用员工"})
            continue
        best = candidates[0]
        staff = db.get(Staff, best["staff_id"])
        try:
            order_service.assign_order(db, order, staff, dispatch_type="ai", score=best["score"])
            dispatched.append(
                {
                    "order_id": order.id,
                    "order_no": order.order_no,
                    "staff_id": staff.id,
                    "staff_name": staff.name,
                    "score": best["score"],
                    "reasons": best["reasons"],
                }
            )
        except BizException as exc:
            failed.append({"order_id": order.id, "order_no": order.order_no, "reason": exc.msg})

    db.commit()
    return {"dispatched": dispatched, "failed": failed, "total": len(dispatched) + len(failed)}