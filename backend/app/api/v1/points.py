from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, require_role
from app.core.exceptions import BizException
from app.core.response import BizCode, ok, page_data
from app.models import User
from app.schemas.points import PointsAdjustIn, PointsRankItem, PointsRecordOut
from app.services import points_service

router = APIRouter(prefix="/points", tags=["积分"])


@router.get("/my", summary="我的积分与流水")
def my_points(
    page: int = Query(default=1, ge=1),
    size: int = Query(default=10, ge=1, le=50),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    records, total = points_service.list_records(db, user, page, size)
    items = [PointsRecordOut(**points_service.record_dict(item)).model_dump(mode="json") for item in records]
    data = page_data(items, total, page, size)
    data["balance"] = user.points_balance
    return ok(data)


@router.get("/ranking", summary="积分排行榜")
def points_ranking(
    limit: int = Query(default=10, ge=1, le=50),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = [PointsRankItem(**item).model_dump(mode="json") for item in points_service.ranking(db, limit)]
    return ok(items)


@router.get("/rules", summary="积分规则")
def points_rules(user=Depends(get_current_user)):
    return ok({"rules": points_service.POINT_RULES})


@router.post("/adjust", summary="管理员调整积分")
def adjust_points(
    payload: PointsAdjustIn,
    user=Depends(require_role("admin")),
    db: Session = Depends(get_db),
):
    if payload.amount == 0:
        raise BizException(BizCode.PARAM_ERROR, "调整分值不能为 0")
    target = db.get(User, payload.user_id)
    if target is None:
        raise BizException(BizCode.NOT_FOUND, "用户不存在")
    record = points_service.add_points(
        db,
        target,
        payload.amount,
        "admin_adjust",
        remark=payload.remark or f"管理员调整 {payload.amount} 分",
    )
    db.commit()
    db.refresh(record)
    return ok(points_service.record_dict(record), "积分调整成功")