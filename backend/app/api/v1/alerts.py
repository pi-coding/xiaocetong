from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.core.exceptions import BizException
from app.core.response import BizCode, ok, page_data
from app.models import Toilet
from app.services import alert_service, order_service

router = APIRouter(prefix="/alerts", tags=["超时预警"])


@router.get("/overdue-toilets", summary="超时未打扫厕所")
def overdue_toilets(
    min_level: int = Query(default=1, ge=1, le=3),
    include_dorm: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    items = alert_service.overdue_toilets(db, min_level, include_dorm)
    start = (page - 1) * size
    return ok(page_data(items[start:start + size], len(items), page, size))


@router.get("/overdue-orders", summary="超时工单")
def overdue_orders(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    rows, total = order_service.query_orders(db, only_timeout=True, page=page, size=size)
    items = [item for item in order_service.to_dicts(db, rows)]
    for item in items:
        item["level_text"] = "严重" if item["priority"] in ("high", "urgent") else "预警"
    return ok(page_data(items, total, page, size))


@router.get("/summary", summary="预警汇总")
def alert_summary(
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return ok(alert_service.summary(db))


@router.post("/{toilet_id}/create-order", summary="超时厕所一键生成清洁工单")
def create_clean_order(
    toilet_id: int,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    toilet = db.get(Toilet, toilet_id)
    if toilet is None:
        raise BizException(BizCode.NOT_FOUND, "厕所不存在")
    data = alert_service.create_clean_order(db, toilet, user)
    return ok(data, "已生成清洁工单，可前往 AI 派单")