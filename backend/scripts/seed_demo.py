import random
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.security import hash_password
from app.db.base import Base
from app.db.database import SessionLocal, engine
from app import models as _models  # noqa: F401
from app.models import (
    CleaningLog,
    DormBinding,
    Evaluation,
    Points,
    ServiceOrder,
    Staff,
    Toilet,
    User,
)

RNG = random.Random(2026)
NOW = datetime.now()

STAFF_SEED = [
    ("staff001", "张桂芳", "A栋", "cleaner", "13800001001"),
    ("staff002", "李秀兰", "A栋", "cleaner", "13800001002"),
    ("staff003", "王建国", "B栋", "cleaner", "13800001003"),
    ("staff004", "刘志强", "A栋,B栋,C栋", "plumber", "13800001004"),
    ("staff005", "陈美玲", "B栋", "cleaner", "13800001005"),
    ("staff006", "赵大勇", "C栋", "cleaner", "13800001006"),
    ("staff007", "周文静", "C栋", "cleaner", "13800001007"),
    ("staff008", "孙立军", "A栋,B栋,C栋,D栋", "all", "13800001008"),
]

STUDENT_SEED = [
    ("2023101", "林晓雨", "D", "301"),
    ("2023102", "陈子豪", "D", "302"),
    ("2023103", "王思远", "D", "303"),
    ("2023104", "李佳怡", "D", "304"),
    ("2023105", "张浩然", "D", "401"),
    ("2023106", "刘诗涵", "D", "402"),
    ("2023107", "黄俊杰", "D", "403"),
    ("2023108", "吴梦琪", "D", "404"),
    ("2023109", "徐子轩", "D", "501"),
    ("2023110", "何雨欣", "D", "502"),
]

CLEAN_ITEMS = "地面,便池,洗手台,异味,耗材补充"
ORDER_TITLES = {
    "unclog": ["蹲位堵塞无法冲水", "下水道反水有异味", "便池水位异常"],
    "clean": ["地面污渍较多", "洗手台积垢", "垃圾桶已满需清理"],
    "repair": ["冲水阀漏水", "门锁损坏无法关闭", "灯管不亮", "水龙头不出水"],
}
ORDER_DESC = {
    "unclog": "蹲位完全堵塞，冲水后水位上涨，请尽快处理。",
    "clean": "地面有明显污渍和积水，气味较重，希望尽快清洁。",
    "repair": "设施损坏影响使用，已拍照上传，请安排维修。",
}
PRIORITY = {"unclog": "high", "repair": "normal", "clean": "low"}


def build_users(db):
    admin = User(
        username="admin",
        password_hash=hash_password("123456"),
        real_name="系统管理员",
        role="admin",
        phone="13900000000",
        points_balance=0,
    )
    db.add(admin)

    staff_rows = []
    for no, name, area, work_type, phone in STAFF_SEED:
        account = User(
            username=no,
            password_hash=hash_password("123456"),
            real_name=name,
            role="staff",
            phone=phone,
            points_balance=0,
        )
        db.add(account)
        db.flush()
        staff = Staff(
            user_id=account.id,
            staff_no=no.upper(),
            name=name,
            phone=phone,
            work_type=work_type,
            area=area,
        )
        db.add(staff)
        db.flush()
        staff_rows.append(staff)

    students = []
    for no, name, building, room in STUDENT_SEED:
        student = User(
            username=no,
            password_hash=hash_password("123456"),
            real_name=name,
            role="student",
            phone=f"137{RNG.randint(10000000, 99999999)}",
            student_no=no,
            building=building,
            room_no=room,
        )
        db.add(student)
        db.flush()
        students.append(student)

    return admin, staff_rows, students


def build_toilets(db, staff_rows):
    cleaners_by_building = {"A": [0, 1], "B": [2, 4], "C": [5, 6]}
    toilets = []
    for building in ("A", "B", "C"):
        for floor in range(1, 6):
            for idx, side in enumerate(("东", "西"), start=1):
                code = f"{building}-{floor}F-{idx:02d}"
                cleaner_pool = cleaners_by_building[building]
                cleaner = staff_rows[cleaner_pool[(floor + idx) % len(cleaner_pool)]]
                last_clean = NOW - timedelta(minutes=RNG.choice([30, 90, 150, 210, 300, 420, 600, 780]))
                status = "normal"
                if RNG.random() < 0.08:
                    status = "dirty"
                elif RNG.random() < 0.05:
                    status = "fault"
                toilet = Toilet(
                    code=code,
                    name=f"{building}栋{floor}层{side}侧公厕",
                    type="public",
                    building=building,
                    floor=floor,
                    location_desc=f"{building}栋{floor}层走廊尽头{side}侧",
                    gender="male" if idx == 1 else "female",
                    stall_count=RNG.randint(4, 8),
                    status=status,
                    cleaner_id=cleaner.id,
                    clean_interval_min=240,
                    last_cleaned_at=last_clean,
                    avg_score=Decimal(str(round(RNG.uniform(4.0, 5.0), 2))),
                    qr_token=f"CCT-{code}",
                )
                db.add(toilet)
                toilets.append(toilet)

    for no, name, building, room in STUDENT_SEED:
        code = f"{building}-{room}"
        toilet = Toilet(
            code=code,
            name=f"{building}栋{room}宿舍卫生间",
            type="dorm",
            building=building,
            floor=int(room[0]),
            location_desc=f"{building}栋{room}室内",
            gender="all",
            stall_count=1,
            status="normal",
            cleaner_id=staff_rows[7].id,
            clean_interval_min=1440,
            last_cleaned_at=NOW - timedelta(hours=RNG.randint(2, 20)),
            avg_score=Decimal("5.00"),
            qr_token=f"CCT-{code}",
        )
        db.add(toilet)
        toilets.append(toilet)

    db.flush()
    return toilets


def build_bindings(db, students, toilets):
    dorm_toilets = {t.code: t for t in toilets if t.type == "dorm"}
    for student in students:
        toilet = dorm_toilets[f"{student.building}-{student.room_no}"]
        db.add(
            DormBinding(
                user_id=student.id,
                toilet_id=toilet.id,
                building=student.building,
                floor=int(student.room_no[0]),
                room_no=student.room_no,
                bind_type="owner",
                status=1,
            )
        )
    db.flush()


def build_orders(db, students, toilets, staff_rows):
    public_toilets = [t for t in toilets if t.type == "public"]
    plans = [
        ("done", "unclog", "high", 0, 5),
        ("done", "clean", "low", 1, 6),
        ("done", "repair", "normal", 2, 4),
        ("done", "unclog", "urgent", 3, 3),
        ("done", "clean", "normal", 4, 2),
        ("done", "repair", "normal", 5, 2),
        ("done", "clean", "low", 6, 1),
        ("done", "unclog", "high", 7, 1),
        ("done", "clean", "normal", 8, 0),
        ("done", "repair", "high", 9, 0),
        ("processing", "unclog", "urgent", 0, 0),
        ("processing", "clean", "normal", 2, 0),
        ("processing", "repair", "high", 4, 0),
        ("assigned", "clean", "normal", 1, 0),
        ("assigned", "repair", "normal", 3, 0),
        ("pending", "unclog", "high", 5, 0),
        ("pending", "clean", "low", 6, 0),
        ("pending", "repair", "urgent", 8, 0),
        ("cancelled", "clean", "low", 7, 2),
        ("cancelled", "repair", "normal", 9, 3),
    ]
    orders = []
    used_slots = set()
    for index, (status, order_type, priority, student_idx, days_ago) in enumerate(plans, start=1):
        toilet = RNG.choice(public_toilets)
        student = students[student_idx]
        slot = (student.id, toilet.id)
        if slot in used_slots:
            toilet = public_toilets[(public_toilets.index(toilet) + 7) % len(public_toilets)]
            slot = (student.id, toilet.id)
        used_slots.add(slot)

        created = NOW - timedelta(days=days_ago, hours=RNG.randint(1, 9))
        order = ServiceOrder(
            order_no=f"WC{created.strftime('%Y%m%d')}{index:04d}",
            user_id=student.id,
            toilet_id=toilet.id,
            type=order_type,
            title=RNG.choice(ORDER_TITLES[order_type]),
            description=ORDER_DESC[order_type],
            images=None,
            priority=priority,
            status=status,
            expect_finish_at=created + timedelta(hours=4 if priority == "urgent" else 8),
            created_at=created,
            updated_at=created,
        )

        if status in ("assigned", "processing", "done"):
            staff = RNG.choice([s for s in staff_rows if s.work_type in ("cleaner", "all")])
            order.assignee_id = staff.id
            order.dispatch_type = "ai" if index % 3 == 0 else "manual"
            order.dispatch_score = Decimal(str(round(RNG.uniform(70, 96), 2))) if order.dispatch_type == "ai" else None
            order.assigned_at = created + timedelta(minutes=RNG.randint(3, 25))
        if status in ("processing", "done"):
            order.accepted_at = order.assigned_at + timedelta(minutes=RNG.randint(2, 15))
            order.started_at = order.accepted_at + timedelta(minutes=RNG.randint(1, 10))
        if status == "done":
            order.finished_at = order.started_at + timedelta(minutes=RNG.randint(15, 100))
            order.finish_remark = "已按要求处理完毕，现场已清理。"
            order.rating = RNG.choice([3, 4, 4, 5, 5, 5])
            order.updated_at = order.finished_at
            if order.expect_finish_at and order.finished_at > order.expect_finish_at:
                order.is_timeout = 1
        if status == "pending" and order.expect_finish_at and NOW > order.expect_finish_at:
            order.is_timeout = 1

        db.add(order)
        db.flush()
        orders.append(order)

    return orders


def build_evaluations(db, orders):
    eval_map = {}
    comments = [
        "师傅来得很快，处理得很干净。",
        "问题已经解决，态度很好。",
        "处理速度一般，但结果可以接受。",
        "清洁后异味明显改善，点赞。",
    ]
    for order in orders:
        if order.status != "done" or not order.rating:
            continue
        evaluation = Evaluation(
            order_id=order.id,
            user_id=order.user_id,
            staff_id=order.assignee_id,
            toilet_id=order.toilet_id,
            score=order.rating,
            tags="响应快,态度好" if order.rating >= 4 else "处理慢",
            content=RNG.choice(comments),
            created_at=(order.finished_at or NOW) + timedelta(hours=1),
        )
        db.add(evaluation)
        eval_map[order.id] = evaluation
    db.flush()
    return eval_map


def build_cleaning_logs(db, toilets, orders, staff_rows):
    for toilet in toilets:
        for _ in range(2):
            cleaned = (toilet.last_cleaned_at or NOW) - timedelta(minutes=RNG.randint(0, 600))
            staff_id = toilet.cleaner_id or staff_rows[0].id
            db.add(
                CleaningLog(
                    toilet_id=toilet.id,
                    staff_id=staff_id,
                    clean_type="routine",
                    clean_items=CLEAN_ITEMS,
                    duration_min=RNG.randint(8, 25),
                    result="pass",
                    remark="例行保洁完成",
                    cleaned_at=cleaned,
                )
            )
    for order in orders:
        if order.status != "done":
            continue
        db.add(
            CleaningLog(
                toilet_id=order.toilet_id,
                staff_id=order.assignee_id,
                order_id=order.id,
                clean_type="order",
                clean_items=CLEAN_ITEMS,
                duration_min=RNG.randint(10, 60),
                result="pass",
                remark="工单处理完成并复核",
                cleaned_at=order.finished_at or NOW,
            )
        )
    db.flush()


def refresh_stats(db, toilets, orders, staff_rows):
    for toilet in toilets:
        related = [o for o in orders if o.toilet_id == toilet.id]
        toilet.order_count = len(related)
    for staff in staff_rows:
        done = [o for o in orders if o.assignee_id == staff.id and o.status == "done"]
        active = [o for o in orders if o.assignee_id == staff.id and o.status in ("assigned", "processing")]
        staff.done_count = len(done)
        staff.current_load = len(active)
        staff.today_orders = len([o for o in active if o.created_at.date() == NOW.date()])
    db.flush()


def build_points(db, students, orders, eval_map):
    eval_order_ids = set(eval_map.keys())
    for student in students:
        balance = 0
        events = [("admin_adjust", 100, "新用户注册赠送", None, None)]
        for order in orders:
            if order.user_id != student.id:
                continue
            events.append(("order_create", 5, f"提交工单 {order.order_no}", "order", order.id))
            if order.status == "done":
                events.append(("order_done", 10, f"工单完成 {order.order_no}", "order", order.id))
            if order.id in eval_order_ids:
                events.append(("evaluate", 5, "完成服务评价", "evaluation", eval_map[order.id].id))
        for source, amount, remark, ref_type, ref_id in events:
            balance += amount
            db.add(
                Points(
                    user_id=student.id,
                    amount=amount,
                    balance_after=balance,
                    source=source,
                    ref_type=ref_type,
                    ref_id=ref_id,
                    remark=remark,
                    created_at=NOW - timedelta(days=RNG.randint(0, 6)),
                )
            )
        student.points_balance = balance
    db.flush()


def main() -> None:
    force = "--force" in sys.argv
    with SessionLocal() as probe:
        existing = probe.scalar(select(User.id).limit(1))
    if existing and not force:
        print("数据库已有数据，如需重建演示数据请执行：python scripts/seed_demo.py --force")
        return

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    with SessionLocal() as db:
        admin, staff_rows, students = build_users(db)
        toilets = build_toilets(db, staff_rows)
        build_bindings(db, students, toilets)
        orders = build_orders(db, students, toilets, staff_rows)
        eval_map = build_evaluations(db, orders)
        build_cleaning_logs(db, toilets, orders, staff_rows)
        refresh_stats(db, toilets, orders, staff_rows)
        build_points(db, students, orders, eval_map)
        db.commit()

        print("演示数据生成完成")
        print(f"用户 {db.query(User).count()} 个｜厕所 {db.query(Toilet).count()} 个｜工单 {db.query(ServiceOrder).count()} 条")
        print("管理员：admin / 123456")
        print("学生：2023101 ~ 2023110 / 123456")
        print("员工：staff001 ~ staff008 / 123456")


if __name__ == "__main__":
    main()