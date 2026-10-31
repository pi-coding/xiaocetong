from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_role
from app.core.exceptions import BizException
from app.core.response import BizCode, ok, page_data
from app.models import CleaningLog, DormBinding, ServiceOrder, Staff, Toilet
from app.schemas.cleaning import CleaningLogOut
from app.schemas.toilet import ToiletCreateIn, ToiletOut, ToiletQrOut, ToiletUpdateIn
from app.services import cleaning_service
from app.services import toilet_service as svc

router = APIRouter(prefix="/toilets", tags=["厕所台账"])


def _get_toilet(db: Session, toilet_id: int) -> Toilet:
    toilet = db.get(Toilet, toilet_id)
    if toilet is None:
        raise BizException(BizCode.NOT_FOUND, "厕所不存在")
    return toilet


def _single(db: Session, toilet: Toilet) -> dict:
    return ToiletOut(**svc.to_dicts(db, [toilet])[0]).model_dump(mode="json")


@router.get("", summary="厕所列表（分页筛选）")
def list_toilets(
    keyword: Optional[str] = Query(default=None, max_length=50),
    toilet_type: Optional[str] = Query(default=None, alias="type", pattern="^(public|dorm)$"),
    building: Optional[str] = Query(default=None, max_length=32),
    status: Optional[str] = Query(default=None, pattern="^(normal|dirty|fault|maintenance)$"),
    sort: str = Query(default="default", pattern="^(default|score|cleaned)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=12, ge=1, le=100),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows, total = svc.query_toilets(db, keyword, toilet_type, building, status, sort, page, size)
    items = [ToiletOut(**item).model_dump(mode="json") for item in svc.to_dicts(db, rows)]
    return ok(page_data(items, total, page, size))


@router.get("/nearby", summary="附近推荐公共厕所")
def nearby(
    limit: int = Query(default=5, ge=1, le=20),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = [ToiletOut(**item).model_dump(mode="json") for item in svc.nearby_toilets(db, user, limit)]
    return ok(items)


@router.get("/{toilet_id}", summary="厕所详情")
def detail(toilet_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    toilet = _get_toilet(db, toilet_id)
    return ok(_single(db, toilet))


@router.get("/{toilet_id}/qr", summary="厕所二维码标识")
def qr_code(toilet_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    toilet = _get_toilet(db, toilet_id)
    payload = svc.qr_payload(toilet)
    if not toilet.qr_token:
        toilet.qr_token = payload["token"]
        db.commit()
    return ok(ToiletQrOut(**payload).model_dump(mode="json"))


@router.get("/{toilet_id}/cleaning-logs", summary="厕所清洁记录")
def toilet_cleaning_logs(
    toilet_id: int,
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    toilet = _get_toilet(db, toilet_id)
    rows, total = cleaning_service.query_logs(db, toilet_id=toilet.id, page=page, size=size)
    items = [CleaningLogOut(**item).model_dump(mode="json") for item in cleaning_service.to_dicts(db, rows)]
    return ok(page_data(items, total, page, size))


@router.post("", summary="新增厕所台账")
def create_toilet(
    payload: ToiletCreateIn,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    code = payload.code.strip().upper()
    if db.scalar(select(Toilet.id).where(Toilet.code == code)):
        raise BizException(BizCode.DUPLICATE, "厕所编号已存在")
    if payload.cleaner_id and db.get(Staff, payload.cleaner_id) is None:
        raise BizException(BizCode.NOT_FOUND, "负责员工不存在")

    data = payload.model_dump()
    data["code"] = code
    toilet = Toilet(**data, qr_token=f"CCT-{code}")
    db.add(toilet)
    db.commit()
    db.refresh(toilet)
    return ok(_single(db, toilet), "新增成功")


@router.put("/{toilet_id}", summary="编辑厕所台账")
def update_toilet(
    toilet_id: int,
    payload: ToiletUpdateIn,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    toilet = _get_toilet(db, toilet_id)
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("cleaner_id") and db.get(Staff, changes["cleaner_id"]) is None:
        raise BizException(BizCode.NOT_FOUND, "负责员工不存在")
    if changes.get("type") and changes["type"] != toilet.type:
        has_order = db.scalar(select(func.count(ServiceOrder.id)).where(ServiceOrder.toilet_id == toilet.id))
        if has_order:
            raise BizException(BizCode.STATE_ERROR, "该厕所已有工单记录，不能修改类型")
    for field, value in changes.items():
        setattr(toilet, field, value)
    db.commit()
    db.refresh(toilet)
    return ok(_single(db, toilet), "保存成功")


@router.delete("/{toilet_id}", summary="删除厕所台账")
def delete_toilet(
    toilet_id: int,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    toilet = _get_toilet(db, toilet_id)
    order_count = db.scalar(select(func.count(ServiceOrder.id)).where(ServiceOrder.toilet_id == toilet.id))
    binding_count = db.scalar(select(func.count(DormBinding.id)).where(DormBinding.toilet_id == toilet.id))
    log_count = db.scalar(select(func.count(CleaningLog.id)).where(CleaningLog.toilet_id == toilet.id))
    if order_count or binding_count or log_count:
        raise BizException(BizCode.STATE_ERROR, "该厕所存在绑定、工单或清洁记录，不能删除")
    db.delete(toilet)
    db.commit()
    return ok(None, "删除成功")