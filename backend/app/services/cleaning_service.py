from datetime import datetime
from typing import Optional

import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.core.response import BizCode
from app.models import CleaningLog, ServiceOrder, Staff, Toilet, User
from app.schemas.cleaning import CleaningCreateIn
from app.services import order_service

CLEAN_TYPE_TEXT = {"routine": "例行保洁", "order": "工单处理", "emergency": "应急保洁"}
RESULT_TEXT = {"pass": "合格", "fail": "不合格"}


def staff_of_user(db: Session, user: User) -> Optional[Staff]:
    return order_service.staff_of_user(db, user)


def create_log(db: Session, user: User, payload: CleaningCreateIn) -> CleaningLog:
    toilet = db.get(Toilet, payload.toilet_id)
    if toilet is None:
        raise BizException(BizCode.NOT_FOUND, "厕所不存在")

    if user.role == "staff":
        staff = staff_of_user(db, user)
        if staff is None:
            raise BizException(BizCode.NOT_FOUND, "当前账号未关联员工档案")
        if toilet.cleaner_id != staff.id:
            raise BizException(BizCode.FORBIDDEN, "该厕所不在你的责任范围内")
    else:
        if not payload.staff_id:
            raise BizException(BizCode.PARAM_ERROR, "请选择执行的员工")
        staff = db.get(Staff, payload.staff_id)
        if staff is None:
            raise BizException(BizCode.NOT_FOUND, "员工不存在")

    if payload.order_id:
        order = db.get(ServiceOrder, payload.order_id)
        if order is None:
            raise BizException(BizCode.NOT_FOUND, "关联工单不存在")
        if order.toilet_id != toilet.id:
            raise BizException(BizCode.PARAM_ERROR, "关联工单与该厕所不匹配")

    now = datetime.now()
    log = CleaningLog(
        toilet_id=toilet.id,
        staff_id=staff.id,
        order_id=payload.order_id,
        clean_type=payload.clean_type,
        before_images=json.dumps(payload.before_images, ensure_ascii=False) if payload.before_images else None,
        after_images=json.dumps(payload.after_images, ensure_ascii=False) if payload.after_images else None,
        clean_items=",".join(payload.clean_items) if payload.clean_items else None,
        duration_min=payload.duration_min,
        result=payload.result,
        remark=(payload.remark or "").strip() or None,
        cleaned_at=now,
    )
    db.add(log)
    toilet.last_cleaned_at = now
    if toilet.status == "dirty" and payload.result == "pass":
        toilet.status = "normal"
    db.flush()
    return log


def query_logs(
    db: Session,
    toilet_id: Optional[int] = None,
    staff_id: Optional[int] = None,
    result: Optional[str] = None,
    clean_type: Optional[str] = None,
    page: int = 1,
    size: int = 10,
) -> tuple[list[CleaningLog], int]:
    stmt = select(CleaningLog)
    if toilet_id:
        stmt = stmt.where(CleaningLog.toilet_id == toilet_id)
    if staff_id:
        stmt = stmt.where(CleaningLog.staff_id == staff_id)
    if result:
        stmt = stmt.where(CleaningLog.result == result)
    if clean_type:
        stmt = stmt.where(CleaningLog.clean_type == clean_type)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(CleaningLog.cleaned_at.desc(), CleaningLog.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return list(rows), total


def _load_list(value: Optional[str]) -> list[str]:
    if not value:
        return []
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


def to_dicts(db: Session, logs: list[CleaningLog]) -> list[dict]:
    if not logs:
        return []
    toilet_ids = {item.toilet_id for item in logs}
    staff_ids = {item.staff_id for item in logs}
    toilets = {item.id: item for item in db.scalars(select(Toilet).where(Toilet.id.in_(toilet_ids))).all()}
    staffs = {item.id: item for item in db.scalars(select(Staff).where(Staff.id.in_(staff_ids))).all()}

    results = []
    for item in logs:
        toilet = toilets.get(item.toilet_id)
        staff = staffs.get(item.staff_id)
        results.append(
            {
                "id": item.id,
                "toilet_id": item.toilet_id,
                "toilet_name": toilet.name if toilet else None,
                "toilet_code": toilet.code if toilet else None,
                "building": toilet.building if toilet else None,
                "floor": toilet.floor if toilet else None,
                "staff_id": item.staff_id,
                "staff_name": staff.name if staff else None,
                "order_id": item.order_id,
                "clean_type": item.clean_type,
                "clean_type_text": CLEAN_TYPE_TEXT.get(item.clean_type, item.clean_type),
                "clean_items": [part for part in (item.clean_items or "").split(",") if part],
                "before_images": _load_list(item.before_images),
                "after_images": _load_list(item.after_images),
                "duration_min": item.duration_min,
                "result": item.result,
                "remark": item.remark,
                "cleaned_at": item.cleaned_at,
                "created_at": item.created_at,
            }
        )
    return results


def to_dict(db: Session, log: CleaningLog) -> dict:
    return to_dicts(db, [log])[0]