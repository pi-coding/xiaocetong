from datetime import datetime, timedelta
from typing import Optional

import json

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import DormBinding, Evaluation, ServiceOrder, Staff, Toilet, User
from app.schemas.order import OrderCreateIn, OrderFinishIn
from app.services import points_service
from app.utils.order_no import gen_order_no

ACTIVE_STATUS = ("pending", "assigned", "processing")

STATUS_TEXT = {
    "pending": "待派单",
    "assigned": "已派单",
    "processing": "处理中",
    "done": "已完成",
    "closed": "已关闭",
    "cancelled": "已取消",
}

TYPE_TEXT = {"unclog": "通厕所", "clean": "清洁", "repair": "报修"}
PRIORITY_TEXT = {"low": "低", "normal": "普通", "high": "高", "urgent": "紧急"}
SLA_MINUTES = {"urgent": 120, "high": 240, "normal": 480, "low": 1440}
URGE_INTERVAL_MINUTES = 10


def order_timeout(order: ServiceOrder, now: Optional[datetime] = None) -> bool:
    if order.status not in ACTIVE_STATUS:
        return False
    if not order.expect_finish_at:
        return False
    return (now or datetime.now()) > order.expect_finish_at


def staff_of_user(db: Session, user: User) -> Optional[Staff]:
    return db.scalar(select(Staff).where(Staff.user_id == user.id))


def get_order(db: Session, order_id: int) -> ServiceOrder:
    from app.core.exceptions import BizException
    from app.core.response import BizCode

    order = db.get(ServiceOrder, order_id)
    if order is None:
        raise BizException(BizCode.NOT_FOUND, "工单不存在")
    return order


def ensure_visible(db: Session, order: ServiceOrder, user: User) -> Optional[Staff]:
    staff = staff_of_user(db, user)
    if user.role == "admin":
        return staff
    if user.role == "student" and order.user_id == user.id:
        return staff
    if staff is not None and order.assignee_id == staff.id:
        return staff
    from app.core.exceptions import BizException
    from app.core.response import BizCode

    raise BizException(BizCode.FORBIDDEN, "无权查看该工单")


def _release_load(db: Session, order: ServiceOrder) -> None:
    if order.assignee_id:
        staff = db.get(Staff, order.assignee_id)
        if staff is not None and staff.current_load > 0:
            staff.current_load -= 1


def create_order(db: Session, user: User, payload: OrderCreateIn) -> ServiceOrder:
    from app.core.exceptions import BizException
    from app.core.response import BizCode

    toilet = db.get(Toilet, payload.toilet_id)
    if toilet is None:
        raise BizException(BizCode.NOT_FOUND, "厕所不存在")

    if toilet.type == "dorm":
        bound = db.scalar(
            select(DormBinding.id).where(
                DormBinding.user_id == user.id,
                DormBinding.toilet_id == toilet.id,
                DormBinding.status == 1,
            )
        )
        if not bound:
            raise BizException(BizCode.FORBIDDEN, "只能对本人绑定的宿舍厕所提交工单")

    duplicated = db.scalar(
        select(ServiceOrder.id).where(
            ServiceOrder.user_id == user.id,
            ServiceOrder.toilet_id == toilet.id,
            ServiceOrder.status.in_(ACTIVE_STATUS),
        )
    )
    if duplicated:
        raise BizException(BizCode.DUPLICATE, "该厕所已有你未完成的工单，请勿重复提交")

    now = datetime.now()
    order = ServiceOrder(
        order_no=gen_order_no(db),
        user_id=user.id,
        toilet_id=toilet.id,
        type=payload.type,
        title=payload.title.strip(),
        description=(payload.description or "").strip() or None,
        images=json.dumps(payload.images, ensure_ascii=False) if payload.images else None,
        priority=payload.priority,
        status="pending",
        expect_finish_at=now + timedelta(minutes=SLA_MINUTES.get(payload.priority, 480)),
    )
    db.add(order)
    toilet.order_count += 1
    db.flush()
    points_service.add_points(
        db, user, 5, "order_create", "order", order.id, f"提交工单 {order.order_no}"
    )
    db.flush()
    return order


def can_dispatch_staff(staff: Staff, order_type: str) -> bool:
    if staff.work_type == "all":
        return True
    if order_type == "repair":
        return staff.work_type == "plumber"
    return staff.work_type in ("cleaner", "all")


def today_assigned_count(db: Session, staff_id: int) -> int:
    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    return (
        db.scalar(
            select(func.count(ServiceOrder.id)).where(
                ServiceOrder.assignee_id == staff_id,
                ServiceOrder.assigned_at >= start,
            )
        )
        or 0
    )


def assign_order(
    db: Session,
    order: ServiceOrder,
    staff: Staff,
    dispatch_type: str = "manual",
    score: Optional[float] = None,
) -> ServiceOrder:
    from app.core.exceptions import BizException
    from app.core.response import BizCode

    if order.status not in ("pending", "assigned"):
        raise BizException(BizCode.STATE_ERROR, "当前状态不可派单")
    if staff.status != "on":
        raise BizException(BizCode.STATE_ERROR, "该员工当前不在岗")
    if not can_dispatch_staff(staff, order.type):
        raise BizException(BizCode.STATE_ERROR, "该员工工种与工单类型不匹配")
    if today_assigned_count(db, staff.id) >= staff.max_daily_orders:
        raise BizException(BizCode.STATE_ERROR, "该员工今日接单量已达上限")

    now = datetime.now()
    if order.assignee_id and order.assignee_id != staff.id:
        _release_load(db, order)
    elif order.assignee_id == staff.id and order.status == "assigned":
        return order

    order.assignee_id = staff.id
    order.status = "assigned"
    order.dispatch_type = dispatch_type
    order.dispatch_score = score
    order.assigned_at = now
    staff.current_load += 1
    staff.today_orders = today_assigned_count(db, staff.id) + 1
    db.flush()
    return order


def accept_order(db: Session, order: ServiceOrder, staff: Staff) -> ServiceOrder:
    from app.core.exceptions import BizException
    from app.core.response import BizCode

    if order.status != "assigned":
        raise BizException(BizCode.STATE_ERROR, "当前状态不可接单")
    if order.assignee_id != staff.id:
        raise BizException(BizCode.FORBIDDEN, "该工单未指派给你")
    now = datetime.now()
    order.status = "processing"
    order.accepted_at = now
    order.started_at = now
    db.flush()
    return order


def finish_order(db: Session, order: ServiceOrder, staff: Staff, payload: OrderFinishIn) -> ServiceOrder:
    from app.core.exceptions import BizException
    from app.core.response import BizCode


    if order.assignee_id != staff.id:
        raise BizException(BizCode.FORBIDDEN, "该工单未指派给你")
    if order.status != "processing":
        raise BizException(BizCode.STATE_ERROR, "请先接单后再提交完工")

    now = datetime.now()
    order.status = "done"
    order.finished_at = now
    order.finish_remark = (payload.finish_remark or "").strip() or None
    order.finish_images = json.dumps(payload.finish_images, ensure_ascii=False) if payload.finish_images else None
    order.is_timeout = 1 if order.expect_finish_at and now > order.expect_finish_at else 0

    duration = int((now - (order.started_at or order.assigned_at or now)).total_seconds() // 60)
    staff.done_count += 1
    if staff.done_count > 1:
        staff.avg_duration_min = (
            staff.avg_duration_min * (staff.done_count - 1) + duration
        ) / staff.done_count
    else:
        staff.avg_duration_min = duration
    _release_load(db, order)

    toilet = db.get(Toilet, order.toilet_id)
    if toilet is not None and order.type in ("clean", "unclog"):
        toilet.last_cleaned_at = now
        if toilet.status == "dirty":
            toilet.status = "normal"

    reporter = db.get(User, order.user_id)
    if reporter is not None:
        points_service.add_points(
            db, reporter, 10, "order_done", "order", order.id, f"工单完成 {order.order_no}"
        )

    db.flush()
    return order


def cancel_order(db: Session, order: ServiceOrder, user: User) -> ServiceOrder:
    from app.core.exceptions import BizException
    from app.core.response import BizCode

    if order.user_id != user.id:
        raise BizException(BizCode.FORBIDDEN, "只能取消自己的工单")
    if order.status not in ("pending", "assigned"):
        raise BizException(BizCode.STATE_ERROR, "处理中的工单不可取消，请联系管理员")
    _release_load(db, order)
    order.status = "cancelled"
    db.flush()
    return order


def close_order(db: Session, order: ServiceOrder, reason: Optional[str] = None) -> ServiceOrder:
    from app.core.exceptions import BizException
    from app.core.response import BizCode

    if order.status in ("cancelled", "closed"):
        raise BizException(BizCode.STATE_ERROR, "该工单已结束")
    if order.status in ("assigned", "processing"):
        _release_load(db, order)
    order.status = "closed"
    if reason:
        order.finish_remark = reason.strip()[:255]
    db.flush()
    return order


def urge_order(db: Session, order: ServiceOrder) -> ServiceOrder:
    from app.core.exceptions import BizException
    from app.core.response import BizCode

    if order.status not in ACTIVE_STATUS:
        raise BizException(BizCode.STATE_ERROR, "工单已结束，无需催单")
    now = datetime.now()
    if order.last_urged_at and now - order.last_urged_at < timedelta(minutes=URGE_INTERVAL_MINUTES):
        raise BizException(BizCode.STATE_ERROR, f"请 {URGE_INTERVAL_MINUTES} 分钟后再催单")
    order.urge_count += 1
    order.last_urged_at = now
    db.flush()
    return order


def query_orders(
    db: Session,
    user: Optional[User] = None,
    staff: Optional[Staff] = None,
    scope: str = "all",
    status: Optional[str] = None,
    order_type: Optional[str] = None,
    priority: Optional[str] = None,
    keyword: Optional[str] = None,
    toilet_id: Optional[int] = None,
    assignee_id: Optional[int] = None,
    only_timeout: bool = False,
    page: int = 1,
    size: int = 10,
) -> tuple[list[ServiceOrder], int]:
    stmt = select(ServiceOrder)

    if scope == "mine" and user is not None:
        stmt = stmt.where(ServiceOrder.user_id == user.id)
    if scope == "staff" and staff is not None:
        stmt = stmt.where(
            ServiceOrder.assignee_id == staff.id,
            ServiceOrder.status.in_(("assigned", "processing")),
        )
    if status:
        stmt = stmt.where(ServiceOrder.status == status)
    if order_type:
        stmt = stmt.where(ServiceOrder.type == order_type)
    if priority:
        stmt = stmt.where(ServiceOrder.priority == priority)
    if toilet_id:
        stmt = stmt.where(ServiceOrder.toilet_id == toilet_id)
    if assignee_id:
        stmt = stmt.where(ServiceOrder.assignee_id == assignee_id)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(
            ServiceOrder.title.like(pattern) | ServiceOrder.order_no.like(pattern)
        )
    if only_timeout:
        stmt = stmt.where(
            ServiceOrder.status.in_(ACTIVE_STATUS),
            ServiceOrder.expect_finish_at.is_not(None),
            ServiceOrder.expect_finish_at < datetime.now(),
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    rows = db.scalars(
        stmt.order_by(ServiceOrder.created_at.desc(), ServiceOrder.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return list(rows), total


def _maps(db: Session, orders: list[ServiceOrder]) -> tuple[dict, dict, dict]:
    toilet_ids = {item.toilet_id for item in orders}
    staff_ids = {item.assignee_id for item in orders if item.assignee_id}
    user_ids = {item.user_id for item in orders}

    toilets = {
        item.id: item
        for item in db.scalars(select(Toilet).where(Toilet.id.in_(toilet_ids))).all()
    } if toilet_ids else {}
    staffs = {
        item.id: item
        for item in db.scalars(select(Staff).where(Staff.id.in_(staff_ids))).all()
    } if staff_ids else {}
    users = {
        item.id: item
        for item in db.scalars(select(User).where(User.id.in_(user_ids))).all()
    } if user_ids else {}
    return toilets, staffs, users


def _load_list(value: Optional[str]) -> list[str]:

    if not value:
        return []
    try:
        data = json.loads(value)
        return data if isinstance(data, list) else []
    except (ValueError, TypeError):
        return []


def to_dict(
    order: ServiceOrder,
    toilet: Optional[Toilet] = None,
    assignee: Optional[Staff] = None,
    reporter: Optional[User] = None,
    viewer: Optional[User] = None,
    has_evaluation: bool = False,
    now: Optional[datetime] = None,
) -> dict:
    from decimal import Decimal

    now = now or datetime.now()
    can_cancel = bool(viewer and viewer.role == "student" and order.user_id == viewer.id and order.status in ("pending", "assigned"))
    can_urge = bool(viewer and viewer.role == "student" and order.user_id == viewer.id and order.status in ACTIVE_STATUS)
    can_evaluate = bool(
        viewer
        and viewer.role == "student"
        and order.user_id == viewer.id
        and order.status == "done"
        and not has_evaluation
    )
    return {
        "id": order.id,
        "order_no": order.order_no,
        "type": order.type,
        "type_text": TYPE_TEXT.get(order.type, order.type),
        "title": order.title,
        "description": order.description,
        "images": _load_list(order.images),
        "priority": order.priority,
        "priority_text": PRIORITY_TEXT.get(order.priority, order.priority),
        "status": order.status,
        "status_text": STATUS_TEXT.get(order.status, order.status),
        "toilet_id": order.toilet_id,
        "toilet_code": toilet.code if toilet else None,
        "toilet_name": toilet.name if toilet else None,
        "building": toilet.building if toilet else None,
        "floor": toilet.floor if toilet else None,
        "location_desc": toilet.location_desc if toilet else None,
        "user_id": order.user_id,
        "user_name": reporter.real_name if reporter else None,
        "user_phone": reporter.phone if reporter else None,
        "assignee_id": order.assignee_id,
        "assignee_name": assignee.name if assignee else None,
        "assignee_phone": assignee.phone if assignee else None,
        "dispatch_type": order.dispatch_type,
        "dispatch_score": float(order.dispatch_score) if isinstance(order.dispatch_score, Decimal) else order.dispatch_score,
        "expect_finish_at": order.expect_finish_at,
        "created_at": order.created_at,
        "assigned_at": order.assigned_at,
        "accepted_at": order.accepted_at,
        "started_at": order.started_at,
        "finished_at": order.finished_at,
        "finish_images": _load_list(order.finish_images),
        "finish_remark": order.finish_remark,
        "is_timeout": order.is_timeout,
        "urge_count": order.urge_count,
        "rating": order.rating,
        "can_cancel": can_cancel,
        "can_urge": can_urge,
        "can_evaluate": can_evaluate,
    }


def to_dicts(db: Session, orders: list[ServiceOrder], viewer: Optional[User] = None) -> list[dict]:
    if not orders:
        return []
    toilets, staffs, users = _maps(db, orders)
    evaluated = set(
        db.scalars(
            select(Evaluation.order_id).where(Evaluation.order_id.in_([item.id for item in orders]))
        ).all()
    )
    now = datetime.now()
    return [
        to_dict(
            item,
            toilets.get(item.toilet_id),
            staffs.get(item.assignee_id),
            users.get(item.user_id),
            viewer,
            item.id in evaluated,
            now,
        )
        for item in orders
    ]


def build_timeline(order: ServiceOrder, has_evaluation: bool = False) -> list[dict]:
    nodes = [
        {"key": "created", "title": "提交工单", "time": order.created_at, "desc": "工单已受理，等待派单"},
    ]
    if order.assigned_at:
        nodes.append({"key": "assigned", "title": "已派单", "time": order.assigned_at, "desc": None})
    if order.accepted_at:
        nodes.append({"key": "accepted", "title": "员工接单", "time": order.accepted_at, "desc": None})
    if order.finished_at:
        nodes.append({"key": "finished", "title": "处理完成", "time": order.finished_at, "desc": order.finish_remark})
    if order.status == "cancelled":
        nodes.append({"key": "cancelled", "title": "工单已取消", "time": None, "desc": "报单人取消了工单"})
    if order.status == "closed":
        nodes.append({"key": "closed", "title": "工单已关闭", "time": None, "desc": order.finish_remark})
    if has_evaluation:
        nodes.append({"key": "evaluated", "title": "已完成评价", "time": None, "desc": None})
    return nodes