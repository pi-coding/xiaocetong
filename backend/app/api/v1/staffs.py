from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.core.exceptions import BizException
from app.core.response import BizCode, ok, page_data
from app.core.security import hash_password
from app.models import CleaningLog, Evaluation, ServiceOrder, Staff, Toilet, User
from app.schemas.order import StaffOptionOut
from app.schemas.points import StaffProfileOut
from app.schemas.staff import StaffAdminOut, StaffCreateIn, StaffUpdateIn
from app.schemas.toilet import ToiletOut
from app.services import order_service, toilet_service

router = APIRouter(prefix="/staffs", tags=["员工"])

ACTIVE_STATUS = ("pending", "assigned", "processing")


def _current_staff(db: Session, user) -> Staff:
    staff = order_service.staff_of_user(db, user)
    if staff is None:
        raise BizException(BizCode.NOT_FOUND, "当前账号未关联员工档案")
    return staff


def _toilet_count(db: Session, staff_id: int) -> int:
    return db.scalar(select(func.count(Toilet.id)).where(Toilet.cleaner_id == staff_id)) or 0


def _account_map(db: Session, staff_rows: list[Staff]) -> dict[int, str]:
    ids = {item.user_id for item in staff_rows if item.user_id}
    if not ids:
        return {}
    rows = db.execute(select(User.id, User.username).where(User.id.in_(ids))).all()
    return {row[0]: row[1] for row in rows}


def _admin_dict(staff: Staff, toilet_count: int, account: Optional[str] = None) -> dict:
    return StaffAdminOut(
        id=staff.id,
        staff_no=staff.staff_no,
        name=staff.name,
        phone=staff.phone,
        work_type=staff.work_type,
        area=staff.area,
        status=staff.status,
        current_load=staff.current_load,
        today_orders=staff.today_orders,
        done_count=staff.done_count,
        avg_score=float(staff.avg_score or 0),
        avg_duration_min=float(staff.avg_duration_min or 0),
        max_daily_orders=staff.max_daily_orders,
        toilet_count=toilet_count,
        user_id=staff.user_id,
        account=account,
    ).model_dump(mode="json")


@router.get("/options", summary="员工下拉选项")
def staff_options(user=Depends(require_role("admin")), db: Session = Depends(get_db)):
    rows = db.scalars(
        select(Staff).order_by(Staff.status.asc(), Staff.current_load.asc(), Staff.id.asc())
    ).all()
    items = [
        StaffOptionOut(
            id=item.id,
            staff_no=item.staff_no,
            name=item.name,
            phone=item.phone,
            work_type=item.work_type,
            area=item.area,
            status=item.status,
            current_load=item.current_load,
            max_daily_orders=item.max_daily_orders,
            avg_score=float(item.avg_score or 0),
        ).model_dump(mode="json")
        for item in rows
    ]
    return ok(items)


@router.get("/me", summary="员工个人档案")
def my_profile(user=Depends(require_role("staff")), db: Session = Depends(get_db)):
    staff = _current_staff(db, user)
    data = StaffProfileOut(
        id=staff.id,
        staff_no=staff.staff_no,
        name=staff.name,
        phone=staff.phone,
        work_type=staff.work_type,
        area=staff.area,
        status=staff.status,
        current_load=staff.current_load,
        today_orders=staff.today_orders,
        done_count=staff.done_count,
        avg_score=float(staff.avg_score or 0),
        avg_duration_min=float(staff.avg_duration_min or 0),
        toilet_count=_toilet_count(db, staff.id),
    )
    return ok(data.model_dump(mode="json"))


@router.get("/my-toilets", summary="我负责的厕所")
def my_toilets(user=Depends(require_role("staff")), db: Session = Depends(get_db)):
    staff = _current_staff(db, user)
    rows = db.scalars(
        select(Toilet)
        .where(Toilet.cleaner_id == staff.id)
        .order_by(Toilet.building.asc(), Toilet.floor.asc(), Toilet.code.asc())
    ).all()
    items = [ToiletOut(**item).model_dump(mode="json") for item in toilet_service.to_dicts(db, list(rows))]
    return ok(items)


@router.get("", summary="员工列表")
def list_staffs(
    keyword: Optional[str] = Query(default=None, max_length=50),
    work_type: Optional[str] = Query(default=None, pattern="^(cleaner|plumber|all)$"),
    status: Optional[str] = Query(default=None, pattern="^(on|off)$"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    stmt = select(Staff)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(Staff.name.like(pattern), Staff.staff_no.like(pattern), Staff.phone.like(pattern))
        )
    if work_type:
        stmt = stmt.where(Staff.work_type == work_type)
    if status:
        stmt = stmt.where(Staff.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(Staff.status.asc(), Staff.id.asc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    accounts = _account_map(db, list(rows))
    items = [
        _admin_dict(item, _toilet_count(db, item.id), accounts.get(item.user_id))
        for item in rows
    ]
    return ok(page_data(items, total, page, size))


@router.post("", summary="新增员工")
def create_staff(
    payload: StaffCreateIn,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    staff_no = payload.staff_no.strip().upper()
    if db.scalar(select(Staff.id).where(Staff.staff_no == staff_no)):
        raise BizException(BizCode.DUPLICATE, "工号已存在")

    account = None
    account_id = None
    if payload.username:
        username = payload.username.strip()
        if db.scalar(select(User.id).where(User.username == username)):
            raise BizException(BizCode.DUPLICATE, "登录账号已存在")
        account = User(
            username=username,
            password_hash=hash_password("123456"),
            real_name=payload.name.strip(),
            role="staff",
            phone=payload.phone,
        )
        db.add(account)
        db.flush()
        account_id = account.id

    staff = Staff(
        user_id=account_id,
        staff_no=staff_no,
        name=payload.name.strip(),
        phone=payload.phone.strip(),
        work_type=payload.work_type,
        area=(payload.area or "").strip() or None,
        status=payload.status,
        max_daily_orders=payload.max_daily_orders,
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    message = "新增成功，登录账号默认密码 123456" if account else "新增成功"
    return ok(_admin_dict(staff, 0, account.username if account else None), message)


@router.put("/{staff_id}", summary="编辑员工")
def update_staff(
    staff_id: int,
    payload: StaffUpdateIn,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    staff = db.get(Staff, staff_id)
    if staff is None:
        raise BizException(BizCode.NOT_FOUND, "员工不存在")
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("name") is None:
        changes.pop("name", None)
    for field, value in changes.items():
        if field == "area" and value is not None:
            value = value.strip() or None
        setattr(staff, field, value)
    if staff.user_id:
        account = db.get(User, staff.user_id)
        if account is not None:
            if changes.get("name"):
                account.real_name = staff.name
            if changes.get("phone"):
                account.phone = staff.phone
    db.commit()
    db.refresh(staff)
    accounts = _account_map(db, [staff])
    return ok(_admin_dict(staff, _toilet_count(db, staff.id), accounts.get(staff.user_id)), "保存成功")


@router.put("/{staff_id}/status", summary="员工上下岗")
def toggle_staff_status(
    staff_id: int,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    staff = db.get(Staff, staff_id)
    if staff is None:
        raise BizException(BizCode.NOT_FOUND, "员工不存在")
    staff.status = "off" if staff.status == "on" else "on"
    db.commit()
    db.refresh(staff)
    accounts = _account_map(db, [staff])
    message = "已设为在岗" if staff.status == "on" else "已设为离岗"
    return ok(_admin_dict(staff, _toilet_count(db, staff.id), accounts.get(staff.user_id)), message)


@router.delete("/{staff_id}", summary="删除员工")
def delete_staff(
    staff_id: int,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    staff = db.get(Staff, staff_id)
    if staff is None:
        raise BizException(BizCode.NOT_FOUND, "员工不存在")

    active_orders = db.scalar(
        select(func.count(ServiceOrder.id)).where(
            ServiceOrder.assignee_id == staff.id, ServiceOrder.status.in_(ACTIVE_STATUS)
        )
    ) or 0
    if active_orders:
        raise BizException(BizCode.STATE_ERROR, "该员工仍有未完成工单，请先改派")
    history_orders = db.scalar(select(func.count(ServiceOrder.id)).where(ServiceOrder.assignee_id == staff.id)) or 0
    if history_orders:
        raise BizException(BizCode.STATE_ERROR, "该员工存在历史工单，不能删除，请改为离岗")
    toilets = _toilet_count(db, staff.id)
    if toilets:
        raise BizException(BizCode.STATE_ERROR, "该员工仍负责厕所，请先在台账调整责任保洁")
    logs = db.scalar(select(func.count(CleaningLog.id)).where(CleaningLog.staff_id == staff.id)) or 0
    if logs:
        raise BizException(BizCode.STATE_ERROR, "该员工存在清洁记录，不能删除，请改为离岗")
    evaluations = db.scalar(select(func.count(Evaluation.id)).where(Evaluation.staff_id == staff.id)) or 0
    if evaluations:
        raise BizException(BizCode.STATE_ERROR, "该员工存在服务评价，不能删除，请改为离岗")

    db.delete(staff)
    db.commit()
    return ok(None, "删除成功，登录账号保留")