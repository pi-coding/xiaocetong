from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_role
from app.core.exceptions import BizException
from app.core.response import BizCode, ok, page_data
from app.models import CleaningLog
from app.schemas.cleaning import CleaningCreateIn, CleaningLogOut
from app.services import cleaning_service, order_service

router = APIRouter(prefix="/cleaning-logs", tags=["清洁记录"])


@router.get("", summary="清洁记录列表")
def list_logs(
    toilet_id: Optional[int] = Query(default=None, ge=1),
    staff_id: Optional[int] = Query(default=None, ge=1),
    result: Optional[str] = Query(default=None, pattern="^(pass|fail)$"),
    clean_type: Optional[str] = Query(default=None, pattern="^(routine|order|emergency)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    rows, total = cleaning_service.query_logs(db, toilet_id, staff_id, result, clean_type, page, size)
    items = [CleaningLogOut(**item).model_dump(mode="json") for item in cleaning_service.to_dicts(db, rows)]
    return ok(page_data(items, total, page, size))


@router.get("/my", summary="我的清洁打卡记录")
def my_logs(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    user=Depends(require_role("staff")),
    db: Session = Depends(get_db),
):
    staff = order_service.staff_of_user(db, user)
    if staff is None:
        raise BizException(BizCode.NOT_FOUND, "当前账号未关联员工档案")
    rows, total = cleaning_service.query_logs(db, staff_id=staff.id, page=page, size=size)
    items = [CleaningLogOut(**item).model_dump(mode="json") for item in cleaning_service.to_dicts(db, rows)]
    return ok(page_data(items, total, page, size))


@router.post("", summary="提交保洁打卡")
def create_log(
    payload: CleaningCreateIn,
    user=Depends(require_role("staff", "admin")),
    db: Session = Depends(get_db),
):
    log = cleaning_service.create_log(db, user, payload)
    db.commit()
    db.refresh(log)
    return ok(CleaningLogOut(**cleaning_service.to_dict(db, log)).model_dump(mode="json"), "打卡成功")


@router.get("/{log_id}", summary="清洁记录详情")
def log_detail(log_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    log = db.get(CleaningLog, log_id)
    if log is None:
        raise BizException(BizCode.NOT_FOUND, "清洁记录不存在")
    return ok(CleaningLogOut(**cleaning_service.to_dict(db, log)).model_dump(mode="json"))