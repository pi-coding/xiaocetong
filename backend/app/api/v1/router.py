from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.v1 import (
    ai,
    alerts,
    auth,
    cleaning_logs,
    dorm_bindings,
    evaluations,
    files,
    orders,
    points,
    staffs,
    stats,
    toilets,
)
from app.core.config import settings
from app.core.deps import get_db
from app.core.response import ok

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(toilets.router)
api_router.include_router(dorm_bindings.router)
api_router.include_router(orders.router)
api_router.include_router(staffs.router)
api_router.include_router(alerts.router)
api_router.include_router(cleaning_logs.router)
api_router.include_router(evaluations.router)
api_router.include_router(points.router)
api_router.include_router(stats.router)
api_router.include_router(ai.router)
api_router.include_router(files.router)


@api_router.get("/health", tags=["系统"], summary="健康检查")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return ok(
        {
            "status": "ok",
            "app": settings.app_name,
            "version": settings.app_version,
            "database": "sqlite" if settings.is_sqlite else "mysql",
            "server_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }
    )