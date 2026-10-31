from datetime import datetime
from io import BytesIO
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.core.response import ok
from app.services import stats_service

router = APIRouter(prefix="/stats", tags=["统计报表"])


@router.get("/overview", summary="核心指标")
def overview(user=Depends(require_role("admin")), db: Session = Depends(get_db)):
    return ok(stats_service.overview(db))


@router.get("/orders-trend", summary="工单趋势")
def orders_trend(
    days: int = Query(default=7, ge=1, le=90),
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return ok(stats_service.orders_trend(db, days))


@router.get("/type-distribution", summary="类型与状态分布")
def type_distribution(user=Depends(require_role("admin")), db: Session = Depends(get_db)):
    return ok(stats_service.type_distribution(db))


@router.get("/toilet-ranking", summary="厕所排行")
def toilet_ranking(
    limit: int = Query(default=5, ge=1, le=50),
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return ok(stats_service.toilet_ranking(db, limit))


@router.get("/staff-ranking", summary="员工绩效排行")
def staff_ranking(
    limit: int = Query(default=5, ge=1, le=50),
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    return ok(stats_service.staff_ranking(db, limit))


@router.get("/building-heat", summary="楼栋工单热力")
def building_heat(user=Depends(require_role("admin")), db: Session = Depends(get_db)):
    return ok(stats_service.building_heat(db))


@router.get("/evaluation-summary", summary="评价星级分布")
def evaluation_summary(user=Depends(require_role("admin")), db: Session = Depends(get_db)):
    return ok(stats_service.evaluation_summary(db))


@router.get("/export", summary="导出工单明细 CSV")
def export_orders(
    start: Optional[datetime] = Query(default=None),
    end: Optional[datetime] = Query(default=None),
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    content = stats_service.export_orders(db, start, end)
    data = ("\ufeff" + content).encode("utf-8")
    filename = quote(f"校厕通工单明细-{datetime.now():%Y%m%d%H%M}.csv")
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{filename}"}
    return StreamingResponse(
        BytesIO(data),
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )