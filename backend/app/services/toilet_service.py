from datetime import datetime
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import DormBinding, ServiceOrder, Staff, Toilet

STATUS_TEXT = {
    "normal": "正常",
    "dirty": "脏乱待清洁",
    "fault": "设施故障",
    "maintenance": "维护中",
}

GENDER_TEXT = {"male": "男", "female": "女", "all": "通用"}

ACTIVE_ORDER_STATUS = ("pending", "assigned", "processing")


def overview(toilet: Toilet, now: Optional[datetime] = None) -> tuple[int, int, bool]:
    now = now or datetime.now()
    if toilet.last_cleaned_at is None:
        return 0, 3, True
    elapsed = int((now - toilet.last_cleaned_at).total_seconds() // 60)
    overdue = elapsed - toilet.clean_interval_min
    if overdue <= 0:
        return 0, 0, False
    ratio = overdue / max(toilet.clean_interval_min, 1)
    if ratio < 1:
        level = 1
    elif ratio < 2:
        level = 2
    else:
        level = 3
    return overdue, level, False


def staff_name_map(db: Session, staff_ids: list[Optional[int]]) -> dict[int, str]:
    ids = {item for item in staff_ids if item}
    if not ids:
        return {}
    rows = db.execute(select(Staff.id, Staff.name).where(Staff.id.in_(ids))).all()
    return {row[0]: row[1] for row in rows}


def active_order_map(db: Session, toilet_ids: list[int]) -> dict[int, int]:
    if not toilet_ids:
        return {}
    rows = db.execute(
        select(ServiceOrder.toilet_id, func.count(ServiceOrder.id))
        .where(ServiceOrder.toilet_id.in_(toilet_ids), ServiceOrder.status.in_(ACTIVE_ORDER_STATUS))
        .group_by(ServiceOrder.toilet_id)
    ).all()
    return {row[0]: row[1] for row in rows}


def bound_count_map(db: Session, toilet_ids: list[int]) -> dict[int, int]:
    if not toilet_ids:
        return {}
    rows = db.execute(
        select(DormBinding.toilet_id, func.count(DormBinding.id))
        .where(DormBinding.toilet_id.in_(toilet_ids), DormBinding.status == 1)
        .group_by(DormBinding.toilet_id)
    ).all()
    return {row[0]: row[1] for row in rows}


def toilet_dict(
    toilet: Toilet,
    cleaner_name: Optional[str] = None,
    active_order_count: int = 0,
    bound_count: int = 0,
    now: Optional[datetime] = None,
) -> dict:
    overdue, level, never_cleaned = overview(toilet, now)
    return {
        "id": toilet.id,
        "code": toilet.code,
        "name": toilet.name,
        "type": toilet.type,
        "building": toilet.building,
        "floor": toilet.floor,
        "location_desc": toilet.location_desc,
        "gender": toilet.gender,
        "gender_text": GENDER_TEXT.get(toilet.gender, toilet.gender),
        "stall_count": toilet.stall_count,
        "status": toilet.status,
        "status_text": STATUS_TEXT.get(toilet.status, toilet.status),
        "cleaner_id": toilet.cleaner_id,
        "cleaner_name": cleaner_name,
        "clean_interval_min": toilet.clean_interval_min,
        "last_cleaned_at": toilet.last_cleaned_at,
        "avg_score": float(toilet.avg_score or 0),
        "order_count": toilet.order_count,
        "qr_token": toilet.qr_token,
        "remark": toilet.remark,
        "overdue_minutes": overdue,
        "warn_level": level,
        "never_cleaned": never_cleaned,
        "active_order_count": active_order_count,
        "bound_count": bound_count,
        "created_at": toilet.created_at,
    }


def to_dicts(db: Session, toilets: list[Toilet]) -> list[dict]:
    ids = [item.id for item in toilets]
    names = staff_name_map(db, [item.cleaner_id for item in toilets])
    active = active_order_map(db, ids)
    bound = bound_count_map(db, ids)
    now = datetime.now()
    return [
        toilet_dict(item, names.get(item.cleaner_id), active.get(item.id, 0), bound.get(item.id, 0), now)
        for item in toilets
    ]


def query_toilets(
    db: Session,
    keyword: Optional[str] = None,
    toilet_type: Optional[str] = None,
    building: Optional[str] = None,
    status: Optional[str] = None,
    sort: str = "default",
    page: int = 1,
    size: int = 12,
) -> tuple[list[Toilet], int]:
    stmt = select(Toilet)
    if keyword:
        pattern = f"%{keyword.strip()}%"
        stmt = stmt.where(
            or_(
                Toilet.name.like(pattern),
                Toilet.code.like(pattern),
                Toilet.location_desc.like(pattern),
                Toilet.building.like(pattern),
            )
        )
    if toilet_type:
        stmt = stmt.where(Toilet.type == toilet_type)
    if building:
        stmt = stmt.where(Toilet.building == building)
    if status:
        stmt = stmt.where(Toilet.status == status)

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    if sort == "score":
        order = [Toilet.avg_score.desc(), Toilet.order_count.desc(), Toilet.id]
    elif sort == "cleaned":
        order = [Toilet.last_cleaned_at.desc(), Toilet.id]
    else:
        order = [Toilet.building.asc(), Toilet.floor.asc(), Toilet.code.asc()]

    rows = db.scalars(stmt.order_by(*order).offset((page - 1) * size).limit(size)).all()
    return list(rows), total


def student_area(db: Session, user) -> tuple[Optional[str], Optional[int]]:
    binding = db.scalar(
        select(DormBinding).where(DormBinding.user_id == user.id, DormBinding.status == 1)
    )
    if binding:
        return binding.building, binding.floor
    return user.building, int(user.room_no[0]) if user.room_no and user.room_no[0].isdigit() else None


def nearby_toilets(db: Session, user, limit: int = 5) -> list[dict]:
    building, floor = student_area(db, user)
    rows = list(db.scalars(select(Toilet).where(Toilet.type == "public")).all())
    if not rows:
        return []

    now = datetime.now()

    def rank(item: Toilet):
        overdue, level, never = overview(item, now)
        floor_gap = abs(item.floor - floor) if floor is not None and item.building == building else 9
        return (
            0 if item.building == building else 1,
            level,
            never,
            floor_gap,
            -float(item.avg_score or 0),
        )

    pick = sorted(rows, key=rank)[: max(1, limit)]
    return to_dicts(db, pick)


def find_dorm_toilet(db: Session, building: str, room_no: str) -> Optional[Toilet]:
    code = f"{building}-{room_no}".upper()
    return db.scalar(select(Toilet).where(Toilet.code == code))


def find_or_create_dorm_toilet(db: Session, building: str, room_no: str, floor: Optional[int] = None) -> Toilet:
    building = building.strip().upper()
    room_no = room_no.strip()
    existing = find_dorm_toilet(db, building, room_no)
    if existing:
        return existing

    if floor is None:
        floor = int(room_no[0]) if room_no and room_no[0].isdigit() else 1

    cleaner = db.scalar(
        select(Staff)
        .where(
            Staff.status == "on",
            Staff.work_type.in_(("cleaner", "all")),
            Staff.area.like(f"%{building}%"),
        )
        .order_by(Staff.current_load.asc(), Staff.id.asc())
    )

    code = f"{building}-{room_no}".upper()
    toilet = Toilet(
        code=code,
        name=f"{building}栋{room_no}宿舍卫生间",
        type="dorm",
        building=building,
        floor=floor,
        location_desc=f"{building}栋{room_no}室内",
        gender="all",
        stall_count=1,
        status="normal",
        cleaner_id=cleaner.id if cleaner else None,
        clean_interval_min=1440,
        avg_score=5.0,
        qr_token=f"CCT-{code}",
    )
    db.add(toilet)
    db.flush()
    return toilet


def qr_payload(toilet: Toilet) -> dict:
    token = toilet.qr_token or f"CCT-{toilet.code}"
    content = f"{settings.frontend_base_url.rstrip('/')}/#/student/toilets/{toilet.id}?t={token}"
    return {
        "toilet_id": toilet.id,
        "code": toilet.code,
        "name": toilet.name,
        "token": token,
        "content": content,
    }