from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_role
from app.core.exceptions import BizException
from app.core.response import BizCode, ok, page_data
from app.models import Evaluation, Staff
from app.schemas.order import (
    DispatchRunIn,
    OrderAssignIn,
    OrderCloseIn,
    OrderCreateIn,
    OrderDetailOut,
    OrderFinishIn,
    OrderOut,
)
from app.services import dispatch_service
from app.services import order_service as svc

router = APIRouter(prefix="/orders", tags=["工单"])

ORDER_TYPE_PATTERN = "^(unclog|clean|repair)$"
STATUS_PATTERN = "^(pending|assigned|processing|done|closed|cancelled)$"


def _out(db: Session, order, viewer) -> dict:
    return OrderOut(**svc.to_dicts(db, [order], viewer)[0]).model_dump(mode="json")


def _staff_required(db: Session, user):
    staff = svc.staff_of_user(db, user)
    if staff is None:
        raise BizException(BizCode.NOT_FOUND, "当前账号未关联员工档案")
    return staff


@router.post("", summary="提交工单")
def create_order(
    payload: OrderCreateIn,
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    order = svc.create_order(db, user, payload)
    db.commit()
    db.refresh(order)
    return ok(_out(db, order, user), "工单已提交，等待派单")


@router.get("/my", summary="我的工单")
def my_orders(
    status: Optional[str] = Query(default=None, pattern=STATUS_PATTERN),
    order_type: Optional[str] = Query(default=None, alias="type", pattern=ORDER_TYPE_PATTERN),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    rows, total = svc.query_orders(
        db, user=user, scope="mine", status=status, order_type=order_type, page=page, size=size
    )
    items = [OrderOut(**item).model_dump(mode="json") for item in svc.to_dicts(db, rows, user)]
    return ok(page_data(items, total, page, size))


@router.get("/staff/my", summary="员工待办工单")
def staff_orders(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    user=Depends(require_role("staff")),
    db: Session = Depends(get_db),
):
    staff = _staff_required(db, user)
    rows, total = svc.query_orders(db, staff=staff, scope="staff", page=page, size=size)
    items = [OrderOut(**item).model_dump(mode="json") for item in svc.to_dicts(db, rows, user)]
    return ok(page_data(items, total, page, size))


@router.get("", summary="工单列表（管理端）")
def list_orders(
    status: Optional[str] = Query(default=None, pattern=STATUS_PATTERN),
    order_type: Optional[str] = Query(default=None, alias="type", pattern=ORDER_TYPE_PATTERN),
    priority: Optional[str] = Query(default=None, pattern="^(low|normal|high|urgent)$"),
    keyword: Optional[str] = Query(default=None, max_length=50),
    toilet_id: Optional[int] = Query(default=None, ge=1),
    assignee_id: Optional[int] = Query(default=None, ge=1),
    only_timeout: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=100),
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    rows, total = svc.query_orders(
        db,
        user=user,
        scope="all",
        status=status,
        order_type=order_type,
        priority=priority,
        keyword=keyword,
        toilet_id=toilet_id,
        assignee_id=assignee_id,
        only_timeout=only_timeout,
        page=page,
        size=size,
    )
    items = [OrderOut(**item).model_dump(mode="json") for item in svc.to_dicts(db, rows, user)]
    return ok(page_data(items, total, page, size))


@router.get("/ai-dispatch/suggest", summary="AI 派单推荐")
def dispatch_suggest(
    order_id: Optional[int] = Query(default=None, ge=1),
    limit: int = Query(default=3, ge=1, le=5),
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if order_id:
        order = svc.get_order(db, order_id)
        if order.status not in ("pending", "assigned"):
            raise BizException(BizCode.STATE_ERROR, "该工单当前状态无需派单")
        return ok(dispatch_service.suggest_for_order(db, order, limit))
    return ok(dispatch_service.suggest_all(db, limit))


@router.post("/ai-dispatch", summary="执行 AI 派单")
def run_ai_dispatch(
    payload: DispatchRunIn,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    result = dispatch_service.run_ai_dispatch(db, payload.order_ids)
    message = f"AI 派单完成：成功 {len(result['dispatched'])} 单"
    if result["failed"]:
        message += f"，失败 {len(result['failed'])} 单"
    return ok(result, message)


@router.get("/{order_id}", summary="工单详情")
def order_detail(
    order_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = svc.get_order(db, order_id)
    svc.ensure_visible(db, order, user)
    data = _out(db, order, user)
    has_evaluation = bool(db.scalar(select(Evaluation.id).where(Evaluation.order_id == order.id)))
    data["timeline"] = svc.build_timeline(order, has_evaluation)
    return ok(OrderDetailOut(**data).model_dump(mode="json"))


@router.get("/{order_id}/timeline", summary="工单进度时间线")
def order_timeline(
    order_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = svc.get_order(db, order_id)
    svc.ensure_visible(db, order, user)
    has_evaluation = bool(db.scalar(select(Evaluation.id).where(Evaluation.order_id == order.id)))
    return ok(svc.build_timeline(order, has_evaluation))


@router.post("/{order_id}/assign", summary="派单 / 改派")
def assign_order(
    order_id: int,
    payload: OrderAssignIn,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    order = svc.get_order(db, order_id)
    staff = db.get(Staff, payload.staff_id)
    if staff is None:
        raise BizException(BizCode.NOT_FOUND, "员工不存在")
    svc.assign_order(
        db,
        order,
        staff,
        dispatch_type="ai" if payload.from_ai else "manual",
        score=payload.dispatch_score if payload.from_ai else None,
    )
    db.commit()
    db.refresh(order)
    return ok(_out(db, order, user), f"已派给 {staff.name}")


@router.post("/{order_id}/accept", summary="员工接单")
def accept_order(
    order_id: int,
    user=Depends(require_role("staff")),
    db: Session = Depends(get_db),
):
    staff = _staff_required(db, user)
    order = svc.get_order(db, order_id)
    svc.accept_order(db, order, staff)
    db.commit()
    db.refresh(order)
    return ok(_out(db, order, user), "已接单，请尽快到场处理")


@router.post("/{order_id}/finish", summary="员工提交完工")
def finish_order(
    order_id: int,
    payload: OrderFinishIn,
    user=Depends(require_role("staff")),
    db: Session = Depends(get_db),
):
    staff = _staff_required(db, user)
    order = svc.get_order(db, order_id)
    svc.finish_order(db, order, staff, payload)
    db.commit()
    db.refresh(order)
    return ok(_out(db, order, user), "完工提交成功")


@router.put("/{order_id}/cancel", summary="学生取消工单")
def cancel_order(
    order_id: int,
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    order = svc.get_order(db, order_id)
    svc.cancel_order(db, order, user)
    db.commit()
    db.refresh(order)
    return ok(_out(db, order, user), "工单已取消")


@router.put("/{order_id}/urge", summary="学生催单")
def urge_order(
    order_id: int,
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    order = svc.get_order(db, order_id)
    if order.user_id != user.id:
        raise BizException(BizCode.FORBIDDEN, "只能催自己的工单")
    svc.urge_order(db, order)
    db.commit()
    db.refresh(order)
    return ok(_out(db, order, user), "已催单，后勤会优先处理")


@router.post("/{order_id}/close", summary="管理员关闭工单")
def close_order(
    order_id: int,
    payload: OrderCloseIn,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    order = svc.get_order(db, order_id)
    svc.close_order(db, order, payload.reason)
    db.commit()
    db.refresh(order)
    return ok(_out(db, order, user), "工单已关闭")