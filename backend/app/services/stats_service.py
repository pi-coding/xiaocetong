from datetime import datetime, time, timedelta
from typing import Optional

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models import Evaluation, ServiceOrder, Staff, Toilet, User
from app.services import alert_service, order_service

ACTIVE_STATUS = ("pending", "assigned", "processing")


def _day_start(day) -> datetime:
    return datetime.combine(day, time.min)


def overview(db: Session) -> dict:
    now = datetime.now()
    today = _day_start(now.date())

    toilet_total = db.scalar(select(func.count(Toilet.id))) or 0
    public_total = db.scalar(select(func.count(Toilet.id)).where(Toilet.type == "public")) or 0
    dorm_total = toilet_total - public_total
    avg_toilet_score = db.scalar(select(func.avg(Toilet.avg_score))) or 0

    today_orders = db.scalar(select(func.count(ServiceOrder.id)).where(ServiceOrder.created_at >= today)) or 0
    pending_orders = db.scalar(select(func.count(ServiceOrder.id)).where(ServiceOrder.status == "pending")) or 0
    processing_orders = db.scalar(
        select(func.count(ServiceOrder.id)).where(ServiceOrder.status.in_(("assigned", "processing")))
    ) or 0
    today_done = db.scalar(
        select(func.count(ServiceOrder.id)).where(ServiceOrder.finished_at >= today)
    ) or 0
    overdue_orders = db.scalar(
        select(func.count(ServiceOrder.id)).where(
            ServiceOrder.status.in_(ACTIVE_STATUS),
            ServiceOrder.expect_finish_at.is_not(None),
            ServiceOrder.expect_finish_at < now,
        )
    ) or 0

    overdue_toilets = len(alert_service.overdue_toilets(db))

    eval_count = db.scalar(select(func.count(Evaluation.id))) or 0
    avg_rating = db.scalar(select(func.avg(Evaluation.score))) or 0
    staff_on = db.scalar(select(func.count(Staff.id)).where(Staff.status == "on")) or 0
    avg_duration = db.scalar(select(func.avg(Staff.avg_duration_min)).where(Staff.done_count > 0)) or 0

    return {
        "toilet_total": toilet_total,
        "public_total": public_total,
        "dorm_total": dorm_total,
        "avg_toilet_score": round(float(avg_toilet_score), 2),
        "today_orders": today_orders,
        "pending_orders": pending_orders,
        "processing_orders": processing_orders,
        "today_done": today_done,
        "overdue_orders": overdue_orders,
        "overdue_toilets": overdue_toilets,
        "evaluation_count": eval_count,
        "avg_rating": round(float(avg_rating), 2),
        "staff_on": staff_on,
        "avg_duration_min": round(float(avg_duration), 1),
        "server_time": now,
    }


def orders_trend(db: Session, days: int = 7) -> dict:
    days = max(1, min(days, 90))
    dates = [datetime.now().date() - timedelta(days=offset) for offset in range(days - 1, -1, -1)]
    start = _day_start(dates[0])

    created_rows = db.execute(
        select(func.date(ServiceOrder.created_at), func.count(ServiceOrder.id))
        .where(ServiceOrder.created_at >= start)
        .group_by(func.date(ServiceOrder.created_at))
    ).all()
    finished_rows = db.execute(
        select(func.date(ServiceOrder.finished_at), func.count(ServiceOrder.id))
        .where(ServiceOrder.finished_at >= start)
        .group_by(func.date(ServiceOrder.finished_at))
    ).all()

    created_map = {str(row[0]): row[1] for row in created_rows}
    finished_map = {str(row[0]): row[1] for row in finished_rows}

    labels = []
    created = []
    finished = []
    for day in dates:
        key = day.strftime("%Y-%m-%d")
        labels.append(day.strftime("%m-%d"))
        created.append(created_map.get(key, 0))
        finished.append(finished_map.get(key, 0))

    return {"dates": labels, "created": created, "finished": finished}


def type_distribution(db: Session) -> dict:
    rows = db.execute(
        select(ServiceOrder.type, func.count(ServiceOrder.id)).group_by(ServiceOrder.type)
    ).all()
    types = [
        {"key": row[0], "label": order_service.TYPE_TEXT.get(row[0], row[0]), "value": row[1]}
        for row in rows
    ]
    status_rows = db.execute(
        select(ServiceOrder.status, func.count(ServiceOrder.id)).group_by(ServiceOrder.status)
    ).all()
    statuses = [
        {"key": row[0], "label": order_service.STATUS_TEXT.get(row[0], row[0]), "value": row[1]}
        for row in status_rows
    ]
    return {"types": types, "statuses": statuses}


def toilet_ranking(db: Session, limit: int = 5) -> list[dict]:
    rows = db.execute(
        select(Toilet.id, Toilet.code, Toilet.name, Toilet.building, Toilet.avg_score, Toilet.order_count)
        .order_by(Toilet.avg_score.desc(), Toilet.order_count.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": row[0],
            "code": row[1],
            "name": row[2],
            "building": row[3],
            "avg_score": round(float(row[4] or 0), 2),
            "order_count": row[5],
        }
        for row in rows
    ]


def staff_ranking(db: Session, limit: int = 5) -> list[dict]:
    rows = db.execute(
        select(
            Staff.id,
            Staff.staff_no,
            Staff.name,
            Staff.work_type,
            Staff.done_count,
            Staff.avg_score,
            Staff.avg_duration_min,
            Staff.current_load,
        )
        .where(Staff.status == "on")
        .order_by(Staff.done_count.desc(), Staff.avg_score.desc())
        .limit(limit)
    ).all()
    return [
        {
            "id": row[0],
            "staff_no": row[1],
            "name": row[2],
            "work_type": row[3],
            "done_count": row[4],
            "avg_score": round(float(row[5] or 0), 2),
            "avg_duration_min": round(float(row[6] or 0), 1),
            "current_load": row[7],
        }
        for row in rows
    ]


def building_heat(db: Session) -> list[dict]:
    rows = db.execute(
        select(
            Toilet.building,
            func.count(ServiceOrder.id),
            func.sum(case((ServiceOrder.is_timeout == 1, 1), else_=0)),
            func.count(func.distinct(ServiceOrder.toilet_id)),
        )
        .join(Toilet, Toilet.id == ServiceOrder.toilet_id)
        .group_by(Toilet.building)
        .order_by(Toilet.building)
    ).all()
    return [
        {
            "building": row[0],
            "order_count": row[1] or 0,
            "timeout_count": int(row[2] or 0),
            "toilet_count": row[3] or 0,
        }
        for row in rows
    ]


def export_orders(db: Session, start: Optional[datetime] = None, end: Optional[datetime] = None) -> str:
    stmt = select(ServiceOrder).order_by(ServiceOrder.created_at.desc()).limit(5000)
    if start:
        stmt = stmt.where(ServiceOrder.created_at >= start)
    if end:
        stmt = stmt.where(ServiceOrder.created_at <= end)
    rows = db.scalars(stmt).all()
    items = order_service.to_dicts(db, list(rows))

    header = [
        "工单号", "类型", "标题", "厕所编号", "厕所名称", "楼栋", "楼层",
        "报单人", "处理人", "优先级", "状态", "提交时间", "派单时间", "完成时间",
        "是否超时", "评分", "催单次数",
    ]
    lines = [",".join(header)]
    for item in items:
        row = [
            item["order_no"],
            item["type_text"],
            item["title"],
            item["toilet_code"] or "",
            item["toilet_name"] or "",
            item["building"] or "",
            str(item["floor"] or ""),
            item["user_name"] or "",
            item["assignee_name"] or "待派单",
            item["priority_text"],
            item["status_text"],
            _fmt(item["created_at"]),
            _fmt(item["assigned_at"]),
            _fmt(item["finished_at"]),
            "是" if item.get("is_timeout") else "否",
            str(item["rating"] or ""),
            str(item.get("urge_count") or 0),
        ]
        lines.append(",".join(_escape(cell) for cell in row))
    return "\r\n".join(lines)


def _fmt(value) -> str:
    if not value:
        return ""
    return str(value).replace("T", " ")[:19]


def _escape(value: str) -> str:
    text = str(value)
    if any(char in text for char in (",", '"', "\n", "\r")):
        return '"' + text.replace('"', '""') + '"'
    return text


def evaluation_summary(db: Session) -> dict:
    rows = db.execute(
        select(Evaluation.score, func.count(Evaluation.id)).group_by(Evaluation.score)
    ).all()
    distribution = {score: count for score, count in rows}
    return {
        "distribution": [
            {"score": score, "count": distribution.get(score, 0)} for score in range(1, 6)
        ],
        "total": sum(distribution.values()),
    }