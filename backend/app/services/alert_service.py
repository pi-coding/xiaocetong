from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ServiceOrder, Toilet
from app.services import order_service, toilet_service
from app.utils.order_no import gen_order_no

LEVEL_TEXT = {1: "预警", 2: "严重", 3: "紧急"}
PRIORITY_BY_LEVEL = {1: "normal", 2: "high", 3: "urgent"}


def overdue_toilets(db: Session, min_level: int = 1, include_dorm: bool = False) -> list[dict]:
    stmt = select(Toilet)
    if not include_dorm:
        stmt = stmt.where(Toilet.type == "public")
    rows = list(db.scalars(stmt).all())
    items = toilet_service.to_dicts(db, rows)
    filtered = [item for item in items if item["warn_level"] >= min_level]
    filtered.sort(key=lambda item: (-item["warn_level"], -item["overdue_minutes"]))
    for item in filtered:
        item["level_text"] = LEVEL_TEXT.get(item["warn_level"], "预警")
    return filtered


def level_counts(items: list[dict]) -> dict:
    return {
        "warning": sum(1 for item in items if item["warn_level"] == 1),
        "serious": sum(1 for item in items if item["warn_level"] == 2),
        "urgent": sum(1 for item in items if item["warn_level"] == 3),
    }


def summary(db: Session) -> dict:
    items = overdue_toilets(db, min_level=1)
    counts = level_counts(items)
    overdue_orders = order_service.query_orders(db, only_timeout=True, page=1, size=1)[1]
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_orders = (
        db.scalar(select(func.count(ServiceOrder.id)).where(ServiceOrder.created_at >= today_start))
        or 0
    )
    return {
        "overdue_toilets": {
            "total": len(items),
            "warning": counts["warning"],
            "serious": counts["serious"],
            "urgent": counts["urgent"],
        },
        "overdue_orders": {"total": overdue_orders},
        "today_orders": today_orders,
    }


def create_clean_order(db: Session, toilet: Toilet, operator) -> dict:
    from app.core.exceptions import BizException
    from app.core.response import BizCode

    overdue, level, never_cleaned = toilet_service.overview(toilet)
    if level == 0:
        raise BizException(BizCode.STATE_ERROR, "该厕所当前未超时，无需生成清洁工单")

    duplicated = db.scalar(
        select(ServiceOrder.id).where(
            ServiceOrder.toilet_id == toilet.id,
            ServiceOrder.type == "clean",
            ServiceOrder.status.in_(("pending", "assigned", "processing")),
        )
    )
    if duplicated:
        raise BizException(BizCode.DUPLICATE, "该厕所已有未完成的清洁工单")

    now = datetime.now()
    priority = PRIORITY_BY_LEVEL.get(level, "normal")
    sla_minutes = {"urgent": 120, "high": 240, "normal": 480}.get(priority, 480)
    if never_cleaned:
        description = "该厕所暂无清洁记录，请安排全面保洁。"
    else:
        description = f"该厕所已超过清洁周期 {overdue} 分钟，请尽快安排保洁。"

    order = ServiceOrder(
        order_no=gen_order_no(db),
        user_id=operator.id,
        toilet_id=toilet.id,
        type="clean",
        title=f"超时保洁：{toilet.name}",
        description=description,
        priority=priority,
        status="pending",
        expect_finish_at=now + timedelta(minutes=sla_minutes),
    )
    db.add(order)
    toilet.order_count += 1
    db.commit()
    db.refresh(order)
    return order_service.to_dicts(db, [order])[0]