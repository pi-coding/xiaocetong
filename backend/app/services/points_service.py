from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.core.response import BizCode
from app.models import Points, User

POINT_RULES = [
    {"source": "order_create", "label": "提交工单", "points": 5, "desc": "每提交一张有效工单"},
    {"source": "order_done", "label": "工单处理完成", "points": 10, "desc": "工单处理完成后发放"},
    {"source": "evaluate", "label": "完成服务评价", "points": 5, "desc": "对已完成工单提交评价"},
    {"source": "daily_sign", "label": "每日签到", "points": 2, "desc": "每日首次进入校厕通"},
]

SOURCE_TEXT = {item["source"]: item["label"] for item in POINT_RULES}
SOURCE_TEXT.update({"admin_adjust": "管理员调整", "exchange": "积分兑换"})


def add_points(
    db: Session,
    user: User,
    amount: int,
    source: str,
    ref_type: Optional[str] = None,
    ref_id: Optional[int] = None,
    remark: Optional[str] = None,
) -> Optional[Points]:
    if amount == 0:
        return None
    if user.points_balance + amount < 0:
        raise BizException(BizCode.STATE_ERROR, "积分余额不足")
    user.points_balance += amount
    record = Points(
        user_id=user.id,
        amount=amount,
        balance_after=user.points_balance,
        source=source,
        ref_type=ref_type,
        ref_id=ref_id,
        remark=remark,
    )
    db.add(record)
    db.flush()
    return record


def list_records(db: Session, user: User, page: int = 1, size: int = 10) -> tuple[list[Points], int]:
    total = db.scalar(select(func.count(Points.id)).where(Points.user_id == user.id)) or 0
    rows = db.scalars(
        select(Points)
        .where(Points.user_id == user.id)
        .order_by(Points.created_at.desc(), Points.id.desc())
        .offset((page - 1) * size)
        .limit(size)
    ).all()
    return list(rows), total


def ranking(db: Session, limit: int = 10) -> list[dict]:
    rows = db.execute(
        select(User.id, User.real_name, User.building, User.points_balance)
        .where(User.role == "student", User.status == 1)
        .order_by(User.points_balance.desc(), User.id.asc())
        .limit(limit)
    ).all()
    return [
        {
            "rank": index,
            "user_id": row[0],
            "name": row[1],
            "building": row[2],
            "points_balance": row[3],
        }
        for index, row in enumerate(rows, start=1)
    ]


def record_dict(record: Points) -> dict:
    return {
        "id": record.id,
        "amount": record.amount,
        "balance_after": record.balance_after,
        "source": record.source,
        "source_text": SOURCE_TEXT.get(record.source, record.source),
        "ref_type": record.ref_type,
        "ref_id": record.ref_id,
        "remark": record.remark,
        "created_at": record.created_at,
    }