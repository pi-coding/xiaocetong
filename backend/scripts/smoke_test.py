import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from io import BytesIO

from pydantic import ValidationError
from sqlalchemy import delete, func, select
from starlette.datastructures import Headers, UploadFile

from app.api.v1 import auth, dorm_bindings, toilets
from app.api.v1 import ai as ai_api
from app.api.v1.ai import ChatIn
from app.api.v1 import alerts as alerts_api
from app.api.v1 import cleaning_logs as cleaning_logs_api
from app.api.v1 import evaluations as evaluations_api
from app.api.v1 import files as files_api
from app.api.v1 import orders as orders_api
from app.api.v1 import points as points_api
from app.api.v1 import staffs as staffs_api
from app.api.v1 import stats as stats_api
from app.api.v1.router import health
from app.core.config import settings
from app.core.deps import require_role
from app.core.exceptions import BizException
from app.db.database import SessionLocal
from app.models.user import User
from app.models import CleaningLog, DormBinding, Evaluation, Points, ServiceOrder, Staff, Toilet
from app.schemas.dorm_binding import BindingCreateIn, BindingUpdateIn
from app.schemas.cleaning import CleaningCreateIn
from app.schemas.evaluation import EvaluationCreateIn, EvaluationReplyIn
from app.schemas.points import PointsAdjustIn
from app.schemas.staff import StaffCreateIn, StaffUpdateIn
from app.schemas.order import (
    DispatchRunIn,
    OrderAssignIn,
    OrderCloseIn,
    OrderCreateIn,
    OrderFinishIn,
)
from app.schemas.toilet import ToiletCreateIn, ToiletUpdateIn
from app.schemas.user import LoginIn, PasswordChangeIn, ProfileUpdateIn, RegisterIn
from app.services import ai_service, stats_service, toilet_service

results: list[tuple[str, bool, str]] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((name, condition, detail))


def biz_code(fn) -> tuple[int, str]:
    try:
        fn()
    except BizException as exc:
        return exc.code, exc.msg
    except ValidationError as exc:
        return 1000, f"参数校验失败：{exc.errors()[0]['msg']}"
    return -1, "未抛出业务异常"


def main() -> None:
    with SessionLocal() as db:
        counts = {
            model.__tablename__: db.query(model).count()
            for model in (User, Toilet, ServiceOrder, Evaluation, Points, CleaningLog, DormBinding, Staff)
        }
        check(
            "演示数据完整性",
            counts["user"] >= 19 and counts["toilet"] >= 40 and counts["service_order"] >= 20,
            str(counts),
        )

        stale_titles = ("宿舍地面清洁测试", "AI派单测试", "取消测试", "重复工单", "他人宿舍")
        stale_orders = db.scalars(
            select(ServiceOrder).where(
                ServiceOrder.title.in_(stale_titles) | ServiceOrder.title.like("超时保洁：%")
            )
        ).all()
        if stale_orders:
            for item in stale_orders:
                if item.assignee_id and item.status in ("assigned", "processing"):
                    stale_staff = db.get(Staff, item.assignee_id)
                    if stale_staff and stale_staff.current_load > 0:
                        stale_staff.current_load -= 1
            db.execute(delete(ServiceOrder).where(ServiceOrder.id.in_([item.id for item in stale_orders])))
            db.commit()
            for toilet in db.scalars(select(Toilet)).all():
                toilet.order_count = (
                    db.scalar(select(func.count(ServiceOrder.id)).where(ServiceOrder.toilet_id == toilet.id)) or 0
                )
            db.commit()

        body = health(db)
        check("健康检查", body["code"] == 0 and body["data"]["status"] == "ok", str(body["data"]))

        body = auth.login(LoginIn(username="admin", password="123456"), db)
        admin_token = body["data"]["token"]
        check("管理员登录", body["code"] == 0 and bool(admin_token), body["msg"])

        body = auth.me(db.get(User, body["data"]["user"]["id"]))
        check("获取当前用户", body["code"] == 0 and body["data"]["role"] == "admin", body["msg"])

        code, msg = biz_code(lambda: auth.login(LoginIn(username="admin", password="wrong"), db))
        check("错误密码拦截", code == 1001, msg)

        code, msg = biz_code(lambda: auth.login(LoginIn(username="admin", password=""), db))
        check("空密码参数拦截", code == 1000, msg)

        code, msg = biz_code(lambda: auth.register(
            RegisterIn(username="ab", password="123456", real_name="x"), db
        ))
        check("用户名长度校验", code == 1000, msg)

        db.execute(delete(User).where(User.username == "check_stu_01"))
        db.commit()

        body = auth.register(
            RegisterIn(
                username="check_stu_01", password="123456", real_name="测试同学",
                building="D", room_no="601",
            ),
            db,
        )
        check("学生注册", body["code"] == 0 and body["data"]["role"] == "student", body["msg"])

        code, msg = biz_code(lambda: auth.register(
            RegisterIn(username="check_stu_01", password="123456", real_name="测试同学"), db
        ))
        check("重复注册拦截", code == 2003, msg)

        body = auth.login(LoginIn(username="check_stu_01", password="123456"), db)
        student = db.scalar(select(User).where(User.username == "check_stu_01"))
        check("学生登录", body["code"] == 0 and bool(body["data"]["token"]), body["msg"])

        body = auth.update_me(ProfileUpdateIn(phone="13712345678"), student, db)
        check("修改资料", body["code"] == 0 and body["data"]["phone"] == "13712345678", body["msg"])

        body = auth.change_password(
            PasswordChangeIn(old_password="123456", new_password="abc12345"), student, db
        )
        check("修改密码", body["code"] == 0, body["msg"])

        body = auth.login(LoginIn(username="check_stu_01", password="abc12345"), db)
        check("新密码登录", body["code"] == 0, body["msg"])

        code, msg = biz_code(lambda: auth.change_password(
            PasswordChangeIn(old_password="123456", new_password="abc12345"), student, db
        ))
        check("旧密码失效拦截", code == 1000, msg)

        admin_user = db.scalar(select(User).where(User.role == "admin"))
        code, msg = biz_code(lambda: require_role("admin")(student))
        check("角色权限拦截", code == 1002, msg)

        db.execute(delete(Toilet).where(Toilet.code == "T-TEST-01"))
        db.commit()

        body = toilets.create_toilet(
            ToiletCreateIn(code="T-TEST-01", name="测试公厕", building="E", floor=1, stall_count=4),
            admin_user,
            db,
        )
        test_toilet_id = body["data"]["id"]
        check("新增厕所", body["code"] == 0 and body["data"]["status_text"] == "正常", body["msg"])

        code, msg = biz_code(lambda: toilets.create_toilet(
            ToiletCreateIn(code="T-TEST-01", name="重复编号", building="E", floor=1), admin_user, db
        ))
        check("重复编号拦截", code == 2003, msg)

        body = toilets.update_toilet(test_toilet_id, ToiletUpdateIn(status="dirty", stall_count=6), admin_user, db)
        check("编辑厕所", body["data"]["status_text"] == "脏乱待清洁" and body["data"]["stall_count"] == 6, body["msg"])

        body = toilets.list_toilets(
            keyword="测试公厕", toilet_type=None, building=None, status=None,
            sort="default", page=1, size=12, user=admin_user, db=db,
        )
        check("厕所筛选", body["data"]["total"] >= 1 and body["data"]["list"][0]["code"] == "T-TEST-01", str(body["data"]["total"]))

        body = toilets.list_toilets(
            keyword=None, toilet_type="public", building="A", status=None,
            sort="score", page=1, size=5, user=admin_user, db=db,
        )
        check("公厕分页", body["data"]["total"] >= 10 and len(body["data"]["list"]) == 5, str(body["data"]["total"]))

        body = toilets.detail(test_toilet_id, admin_user, db)
        check("厕所详情", body["data"]["code"] == "T-TEST-01" and body["data"]["gender_text"] == "通用", body["msg"])

        body = toilets.qr_code(test_toilet_id, admin_user, db)
        check("二维码标识", "/#/student/toilets/" in body["data"]["content"], body["data"]["content"])

        body = toilets.nearby(5, admin_user, db)
        check("附近推荐", len(body["data"]) == 5, str(len(body["data"])))

        stale = db.scalar(select(User).where(User.username == "bind_stu_01"))
        if stale:
            db.execute(delete(DormBinding).where(DormBinding.user_id == stale.id))
            db.execute(delete(User).where(User.id == stale.id))
        db.commit()
        for code_value in ("D-601", "D-602"):
            leftover = db.scalar(select(Toilet).where(Toilet.code == code_value))
            if leftover:
                db.execute(delete(DormBinding).where(DormBinding.toilet_id == leftover.id))
                db.execute(delete(Toilet).where(Toilet.id == leftover.id))
        db.commit()

        body = auth.register(
            RegisterIn(username="bind_stu_01", password="123456", real_name="绑定测试", building="D", room_no="601"),
            db,
        )
        binder = db.scalar(select(User).where(User.username == "bind_stu_01"))
        check("绑定测试账号", body["code"] == 0, body["msg"])

        body = dorm_bindings.match_binding("D", "601", binder, db)
        check("宿舍厕所匹配", body["data"]["exists"] is False and body["data"]["code"] == "D-601", str(body["data"]))

        body = dorm_bindings.create_binding(BindingCreateIn(building="D", room_no="601"), binder, db)
        binding_id = body["data"]["id"]
        check(
            "绑定宿舍厕所",
            body["code"] == 0 and body["data"]["toilet"]["code"] == "D-601" and body["data"]["toilet"]["type"] == "dorm",
            body["msg"],
        )

        code, msg = biz_code(lambda: dorm_bindings.create_binding(BindingCreateIn(building="D", room_no="601"), binder, db))
        check("重复绑定拦截", code == 2003, msg)

        body = dorm_bindings.my_binding(binder, db)
        check("查询我的绑定", body["data"] is not None and body["data"]["room_no"] == "601", body["msg"])

        body = dorm_bindings.update_binding(binding_id, BindingUpdateIn(building="D", room_no="602"), binder, db)
        check("换绑宿舍", body["data"]["toilet"]["code"] == "D-602", body["msg"])

        code, msg = biz_code(lambda: dorm_bindings.update_binding(
            binding_id, BindingUpdateIn(building="D", room_no="602"), admin_user, db
        ))
        check("越权换绑拦截", code == 1002, msg)

        body = dorm_bindings.delete_binding(binding_id, binder, db)
        check("解绑宿舍", body["code"] == 0, body["msg"])

        body = dorm_bindings.my_binding(binder, db)
        check("解绑后无绑定", body["data"] is None, body["msg"])

        body = toilets.delete_toilet(test_toilet_id, admin_user, db)
        check("删除厕所", body["code"] == 0, body["msg"])

        code, msg = biz_code(lambda: toilets.detail(test_toilet_id, admin_user, db))
        check("删除后不可见", code == 2001, msg)

        dorm_toilet = db.scalar(select(Toilet).where(Toilet.code == "D-301"))
        student = db.scalar(select(User).where(User.username == "2023101"))
        student_points = student.points_balance
        student_points_max = db.scalar(select(func.max(Points.id))) or 0
        other_student = db.scalar(select(User).where(User.username == "2023102"))
        staff_user = db.scalar(select(User).where(User.username == "staff001"))
        other_staff_user = db.scalar(select(User).where(User.username == "staff002"))
        staff = db.scalar(select(Staff).where(Staff.user_id == staff_user.id))
        toilet_snapshot = (dorm_toilet.order_count, dorm_toilet.last_cleaned_at, dorm_toilet.status)
        staff_snapshot = (staff.done_count, staff.current_load, staff.avg_duration_min)

        body = orders_api.create_order(
            OrderCreateIn(
                toilet_id=dorm_toilet.id, type="clean", title="宿舍地面清洁测试", priority="normal"
            ),
            student,
            db,
        )
        order_id = body["data"]["id"]
        check(
            "学生提交工单",
            body["code"] == 0 and body["data"]["status"] == "pending" and body["data"]["assignee_id"] is None,
            body["msg"],
        )

        code, msg = biz_code(lambda: orders_api.create_order(
            OrderCreateIn(toilet_id=dorm_toilet.id, type="clean", title="重复工单"), student, db
        ))
        check("重复工单拦截", code == 2003, msg)

        code, msg = biz_code(lambda: orders_api.create_order(
            OrderCreateIn(toilet_id=dorm_toilet.id, type="clean", title="他人宿舍"), other_student, db
        ))
        check("他人宿舍下单拦截", code == 1002, msg)

        body = orders_api.my_orders(status=None, order_type=None, page=1, size=10, user=student, db=db)
        check("我的工单列表", any(item["id"] == order_id for item in body["data"]["list"]), str(body["data"]["total"]))

        body = orders_api.order_detail(order_id, student, db)
        check(
            "工单详情时间线",
            body["data"]["timeline"][0]["key"] == "created" and body["data"]["can_cancel"] is True,
            str(len(body["data"]["timeline"])),
        )

        body = orders_api.urge_order(order_id, student, db)
        check("学生催单", body["data"]["urge_count"] == 1, body["msg"])

        code, msg = biz_code(lambda: orders_api.urge_order(order_id, student, db))
        check("催单限频", code == 2002, msg)

        body = orders_api.list_orders(
            status="pending", order_type=None, priority=None, keyword="宿舍地面清洁测试",
            toilet_id=None, assignee_id=None, only_timeout=False, page=1, size=10,
            user=admin_user, db=db,
        )
        check("管理端待派筛选", body["data"]["total"] == 1, str(body["data"]["total"]))

        body = staffs_api.staff_options(admin_user, db)
        check("员工下拉选项", len(body["data"]) == 8, str(len(body["data"])))

        code, msg = biz_code(lambda: orders_api.accept_order(order_id, staff_user, db))
        check("未派单不可接单", code == 2002, msg)

        body = orders_api.assign_order(order_id, OrderAssignIn(staff_id=staff.id), admin_user, db)
        check(
            "管理员派单",
            body["code"] == 0 and body["data"]["status"] == "assigned" and body["data"]["assignee_name"] == staff.name,
            body["msg"],
        )
        check("员工负载增加", staff.current_load == staff_snapshot[1] + 1, str(staff.current_load))

        code, msg = biz_code(lambda: orders_api.accept_order(order_id, other_staff_user, db))
        check("非指派员工接单拦截", code == 1002, msg)

        body = orders_api.staff_orders(page=1, size=10, user=staff_user, db=db)
        check("员工待办列表", any(item["id"] == order_id for item in body["data"]["list"]), str(body["data"]["total"]))

        body = orders_api.accept_order(order_id, staff_user, db)
        check("员工接单", body["data"]["status"] == "processing", body["msg"])

        body = orders_api.finish_order(order_id, OrderFinishIn(finish_remark="已清洁完毕"), staff_user, db)
        check(
            "员工提交完工",
            body["data"]["status"] == "done" and body["data"]["finish_remark"] == "已清洁完毕",
            body["msg"],
        )
        check(
            "完工刷新清洁时间",
            dorm_toilet.last_cleaned_at is not None and dorm_toilet.last_cleaned_at > toilet_snapshot[1],
            str(dorm_toilet.last_cleaned_at),
        )
        check("员工负载释放", staff.current_load == staff_snapshot[1], str(staff.current_load))
        check("员工完成量增加", staff.done_count == staff_snapshot[0] + 1, str(staff.done_count))

        code, msg = biz_code(lambda: orders_api.finish_order(order_id, OrderFinishIn(), staff_user, db))
        check("重复完工拦截", code == 2002, msg)

        body = orders_api.order_detail(order_id, student, db)
        check(
            "完成后状态",
            body["data"]["can_evaluate"] is True and body["data"]["can_cancel"] is False,
            str(body["data"]["can_evaluate"]),
        )

        code, msg = biz_code(lambda: orders_api.order_detail(order_id, other_student, db))
        check("越权查看工单拦截", code == 1002, msg)

        body = orders_api.close_order(order_id, OrderCloseIn(reason="测试关单"), admin_user, db)
        check("管理员关闭工单", body["data"]["status"] == "closed", body["msg"])

        code, msg = biz_code(lambda: orders_api.close_order(order_id, OrderCloseIn(), admin_user, db))
        check("重复关单拦截", code == 2002, msg)

        body = orders_api.create_order(
            OrderCreateIn(toilet_id=dorm_toilet.id, type="repair", title="取消测试", priority="low"),
            student,
            db,
        )
        cancel_id = body["data"]["id"]
        body = orders_api.cancel_order(cancel_id, student, db)
        check("学生取消工单", body["data"]["status"] == "cancelled", body["msg"])

        code, msg = biz_code(lambda: orders_api.cancel_order(cancel_id, student, db))
        check("重复取消拦截", code == 2002, msg)

        upload = UploadFile(
            file=BytesIO(b"\x89PNG\r\n\x1a\n" + b"0" * 64),
            filename="test.png",
            headers=Headers({"content-type": "image/png"}),
        )
        body = files_api.upload_image(upload, student)
        check("图片上传", body["code"] == 0 and body["data"]["url"].startswith("/uploads/"), body["msg"])
        uploaded_file = Path(settings.upload_dir) / body["data"]["url"].split("/")[-1]
        uploaded_file.unlink(missing_ok=True)

        db.execute(delete(ServiceOrder).where(ServiceOrder.id.in_([order_id, cancel_id])))
        dorm_toilet.order_count = toilet_snapshot[0]
        dorm_toilet.last_cleaned_at = toilet_snapshot[1]
        dorm_toilet.status = toilet_snapshot[2]
        staff.done_count = staff_snapshot[0]
        staff.current_load = staff_snapshot[1]
        staff.avg_duration_min = staff_snapshot[2]
        db.execute(delete(Points).where(Points.user_id == student.id, Points.id > student_points_max))
        student.points_balance = student_points
        db.commit()

        body = alerts_api.alert_summary(admin_user, db)
        check(
            "预警汇总",
            body["data"]["overdue_toilets"]["total"] >= 1 and body["data"]["overdue_orders"]["total"] >= 1,
            str(body["data"]),
        )

        body = alerts_api.overdue_toilets(min_level=1, include_dorm=False, page=1, size=20, user=admin_user, db=db)
        check(
            "超时厕所列表",
            body["data"]["total"] >= 1 and body["data"]["list"][0]["level_text"] in ("预警", "严重", "紧急"),
            str(body["data"]["total"]),
        )

        body = alerts_api.overdue_orders(page=1, size=10, user=admin_user, db=db)
        check("超时工单列表", body["data"]["total"] >= 1, str(body["data"]["total"]))

        public_toilets = db.scalars(select(Toilet).where(Toilet.type == "public")).all()
        student_points = student.points_balance
        student_points_max = db.scalar(select(func.max(Points.id))) or 0
        active_clean_toilets = set(
            db.scalars(
                select(ServiceOrder.toilet_id).where(
                    ServiceOrder.type == "clean",
                    ServiceOrder.status.in_(("pending", "assigned", "processing")),
                )
            ).all()
        )
        overdue_toilet = next(
            item
            for item in public_toilets
            if toilet_service.overview(item)[1] >= 1 and item.id not in active_clean_toilets
        )
        fresh_toilet = next(item for item in public_toilets if toilet_service.overview(item)[1] == 0)

        body = orders_api.create_order(
            OrderCreateIn(toilet_id=dorm_toilet.id, type="clean", title="AI派单测试", priority="normal"),
            student,
            db,
        )
        ai_order_id = body["data"]["id"]
        check("AI 测试工单创建", body["code"] == 0, body["msg"])

        body = orders_api.dispatch_suggest(order_id=ai_order_id, limit=3, user=admin_user, db=db)
        candidates = body["data"]["candidates"]
        check(
            "AI 派单建议",
            len(candidates) >= 1 and candidates[0]["score"] >= 0
            and candidates == sorted(candidates, key=lambda item: item["score"], reverse=True),
            str(len(candidates)),
        )
        check(
            "推荐得分可解释",
            len(candidates[0]["reasons"]) >= 2
            and set(candidates[0]["factors"]) == {"idle", "speed", "rating", "area"},
            str(candidates[0]["factors"]),
        )

        best_staff = candidates[0]
        body = orders_api.assign_order(
            ai_order_id,
            OrderAssignIn(
                staff_id=best_staff["staff_id"], from_ai=True, dispatch_score=best_staff["score"]
            ),
            admin_user,
            db,
        )
        check(
            "采纳 AI 推荐派单",
            body["data"]["dispatch_type"] == "ai" and body["data"]["dispatch_score"] == best_staff["score"],
            str(body["data"]["dispatch_type"]),
        )
        ai_order = db.get(ServiceOrder, ai_order_id)
        temp_staff = db.get(Staff, ai_order.assignee_id)
        ai_order.status = "pending"
        ai_order.assignee_id = None
        ai_order.assigned_at = None
        ai_order.dispatch_type = "manual"
        ai_order.dispatch_score = None
        if temp_staff and temp_staff.current_load > 0:
            temp_staff.current_load -= 1
            temp_staff.today_orders = max(0, temp_staff.today_orders - 1)
        db.commit()

        body = orders_api.dispatch_suggest(order_id=None, limit=3, user=admin_user, db=db)
        check(
            "批量派单建议",
            any(item["order"]["id"] == ai_order_id for item in body["data"]),
            str(len(body["data"])),
        )

        body = orders_api.run_ai_dispatch(DispatchRunIn(order_ids=[ai_order_id]), admin_user, db)
        ai_order = db.get(ServiceOrder, ai_order_id)
        check(
            "AI 派单执行",
            bool(body["data"]["dispatched"]) and body["data"]["dispatched"][0]["order_id"] == ai_order_id,
            body["msg"],
        )
        check(
            "AI 派单落库",
            ai_order.status == "assigned"
            and ai_order.dispatch_type == "ai"
            and ai_order.dispatch_score is not None
            and ai_order.assignee_id is not None,
            str(ai_order.dispatch_score),
        )

        body = orders_api.run_ai_dispatch(DispatchRunIn(order_ids=[ai_order_id]), admin_user, db)
        check("重复 AI 派单跳过", body["data"]["total"] == 0, str(body["data"]["total"]))

        body = alerts_api.create_clean_order(overdue_toilet.id, admin_user, db)
        clean_order_id = body["data"]["id"]
        check(
            "超时生成清洁单",
            body["data"]["type"] == "clean" and body["data"]["priority"] in ("normal", "high", "urgent")
            and body["data"]["status"] == "pending",
            body["msg"],
        )

        code, msg = biz_code(lambda: alerts_api.create_clean_order(overdue_toilet.id, admin_user, db))
        check("重复清洁单拦截", code == 2003, msg)

        code, msg = biz_code(lambda: alerts_api.create_clean_order(fresh_toilet.id, admin_user, db))
        check("未超时不可生成", code == 2002, msg)

        ai_staff = db.get(Staff, ai_order.assignee_id) if ai_order.assignee_id else None
        db.execute(delete(ServiceOrder).where(ServiceOrder.id.in_([ai_order_id, clean_order_id])))
        if ai_staff is not None:
            ai_staff.current_load = max(0, ai_staff.current_load - 1)
            ai_staff.today_orders = max(0, ai_staff.today_orders - 1)
        overdue_toilet.order_count = max(0, overdue_toilet.order_count - 1)
        dorm_toilet.order_count = toilet_snapshot[0]
        db.execute(delete(Points).where(Points.user_id == student.id, Points.id > student_points_max))
        student.points_balance = student_points
        db.commit()

        points_before = student.points_balance
        points_max = db.scalar(select(func.max(Points.id))) or 0
        toilet_avg_before = dorm_toilet.avg_score
        staff_full_snapshot = (
            staff.done_count,
            staff.current_load,
            staff.avg_duration_min,
            staff.today_orders,
            staff.avg_score,
        )
        clean_toilet = db.scalar(
            select(Toilet)
            .where(Toilet.cleaner_id == staff.id, Toilet.type == "public")
            .order_by(Toilet.id)
            .limit(1)
        )
        other_toilet = db.scalar(
            select(Toilet)
            .where(Toilet.cleaner_id != staff.id, Toilet.type == "public")
            .order_by(Toilet.id)
            .limit(1)
        )
        clean_toilet_snapshot = (clean_toilet.last_cleaned_at, clean_toilet.status)

        body = staffs_api.my_profile(staff_user, db)
        check(
            "员工个人档案",
            body["data"]["staff_no"] == "STAFF001" and body["data"]["toilet_count"] >= 1,
            str(body["data"]["toilet_count"]),
        )

        body = staffs_api.my_toilets(staff_user, db)
        check(
            "员工负责厕所",
            len(body["data"]) >= 1 and all(item["cleaner_id"] == staff.id for item in body["data"]),
            str(len(body["data"])),
        )

        body = orders_api.create_order(
            OrderCreateIn(toilet_id=dorm_toilet.id, type="clean", title="评价流程测试"),
            student,
            db,
        )
        eval_order_id = body["data"]["id"]
        check("下单积分发放", student.points_balance == points_before + 5, str(student.points_balance))

        orders_api.assign_order(eval_order_id, OrderAssignIn(staff_id=staff.id), admin_user, db)
        orders_api.accept_order(eval_order_id, staff_user, db)
        orders_api.finish_order(eval_order_id, OrderFinishIn(finish_remark="测试完工"), staff_user, db)
        check("完工积分发放", student.points_balance == points_before + 15, str(student.points_balance))

        body = evaluations_api.create_evaluation(
            eval_order_id,
            EvaluationCreateIn(score=4, tags=["响应快", "态度好"], content="测试评价"),
            student,
            db,
        )
        evaluation_id = body["data"]["id"]
        check("提交评价", body["data"]["score"] == 4 and "响应快" in body["data"]["tags"], body["msg"])
        check("评价积分发放", student.points_balance == points_before + 20, str(student.points_balance))
        check(
            "工单评分回写",
            db.get(ServiceOrder, eval_order_id).rating == 4,
            str(db.get(ServiceOrder, eval_order_id).rating),
        )
        check("厕所评分重算", abs(float(dorm_toilet.avg_score) - 4.0) < 0.01, str(dorm_toilet.avg_score))

        code, msg = biz_code(lambda: evaluations_api.create_evaluation(
            eval_order_id, EvaluationCreateIn(score=5), student, db
        ))
        check("重复评价拦截", code == 2003, msg)

        body = orders_api.create_order(
            OrderCreateIn(toilet_id=dorm_toilet.id, type="clean", title="未完成评价测试"), student, db
        )
        pending_id = body["data"]["id"]
        code, msg = biz_code(lambda: evaluations_api.create_evaluation(
            pending_id, EvaluationCreateIn(score=5), student, db
        ))
        check("未完成不可评价", code == 2002, msg)

        code, msg = biz_code(lambda: evaluations_api.create_evaluation(
            eval_order_id, EvaluationCreateIn(score=5), other_student, db
        ))
        check("越权评价拦截", code == 1002, msg)

        body = evaluations_api.list_evaluations(
            score=4, toilet_id=None, staff_id=None, only_appeal=False, page=1, size=10,
            user=admin_user, db=db,
        )
        check("评价列表筛选", any(item["id"] == evaluation_id for item in body["data"]["list"]), str(body["data"]["total"]))

        body = evaluations_api.reply_evaluation(
            evaluation_id, EvaluationReplyIn(reply="感谢反馈，我们会持续改进"), admin_user, db
        )
        check("评价回复", body["data"]["reply"] == "感谢反馈，我们会持续改进", body["msg"])

        body = evaluations_api.appeal_evaluation(evaluation_id, admin_user, db)
        check("评价申诉标记", body["data"]["is_appeal"] == 1, str(body["data"]["is_appeal"]))

        body = cleaning_logs_api.create_log(
            CleaningCreateIn(
                toilet_id=clean_toilet.id,
                clean_items=["地面", "便池", "洗手台"],
                duration_min=20,
                remark="例行保洁",
            ),
            staff_user,
            db,
        )
        log_id = body["data"]["id"]
        check("员工清洁打卡", body["code"] == 0 and body["data"]["clean_type_text"] == "例行保洁", body["msg"])
        check(
            "打卡刷新清洁时间",
            clean_toilet.last_cleaned_at is not None and clean_toilet.last_cleaned_at > clean_toilet_snapshot[0],
            str(clean_toilet.last_cleaned_at),
        )

        code, msg = biz_code(lambda: cleaning_logs_api.create_log(
            CleaningCreateIn(toilet_id=other_toilet.id), staff_user, db
        ))
        check("非责任区打卡拦截", code == 1002, msg)

        body = cleaning_logs_api.list_logs(
            toilet_id=None, staff_id=staff.id, result=None, clean_type=None,
            page=1, size=10, user=admin_user, db=db,
        )
        check("清洁记录列表", any(item["id"] == log_id for item in body["data"]["list"]), str(body["data"]["total"]))

        body = toilets.toilet_cleaning_logs(clean_toilet.id, page=1, size=5, user=student, db=db)
        check("厕所清洁记录", body["data"]["total"] >= 1, str(body["data"]["total"]))

        body = cleaning_logs_api.log_detail(log_id, student, db)
        check(
            "清洁记录详情",
            body["data"]["toilet_id"] == clean_toilet.id and len(body["data"]["clean_items"]) == 3,
            body["msg"],
        )

        body = cleaning_logs_api.my_logs(page=1, size=5, user=staff_user, db=db)
        check("员工打卡记录", any(item["id"] == log_id for item in body["data"]["list"]), str(body["data"]["total"]))

        body = points_api.my_points(page=1, size=10, user=student, db=db)
        check(
            "积分余额与流水",
            body["data"]["balance"] == student.points_balance and body["data"]["total"] >= 3,
            str(body["data"]["balance"]),
        )

        body = points_api.points_ranking(limit=5, user=student, db=db)
        check("积分排行榜", len(body["data"]) == 5 and body["data"][0]["rank"] == 1, str(len(body["data"])))

        body = points_api.points_rules(student)
        check("积分规则", len(body["data"]["rules"]) >= 3, str(len(body["data"]["rules"])))

        body = points_api.adjust_points(
            PointsAdjustIn(user_id=student.id, amount=20, remark="测试加分"), admin_user, db
        )
        check(
            "管理员调整积分",
            body["data"]["amount"] == 20 and student.points_balance == points_before + 45,
            str(student.points_balance),
        )

        code, msg = biz_code(lambda: points_api.adjust_points(
            PointsAdjustIn(user_id=student.id, amount=-5000), admin_user, db
        ))
        check("积分不足拦截", code == 2002, msg)

        db.execute(delete(Evaluation).where(Evaluation.order_id.in_([eval_order_id, pending_id])))
        db.execute(delete(ServiceOrder).where(ServiceOrder.id.in_([eval_order_id, pending_id])))
        db.execute(delete(CleaningLog).where(CleaningLog.id == log_id))
        db.execute(delete(Points).where(Points.user_id == student.id, Points.id > points_max))
        student.points_balance = points_before
        dorm_toilet.avg_score = toilet_avg_before
        dorm_toilet.order_count = toilet_snapshot[0]
        staff.done_count, staff.current_load, staff.avg_duration_min, staff.today_orders, staff.avg_score = staff_full_snapshot
        clean_toilet.last_cleaned_at = clean_toilet_snapshot[0]
        clean_toilet.status = clean_toilet_snapshot[1]
        db.commit()

        body = stats_api.overview(admin_user, db)
        check(
            "统计概览",
            body["data"]["toilet_total"] >= 40 and body["data"]["staff_on"] >= 1,
            str(body["data"]["toilet_total"]),
        )

        body = stats_api.orders_trend(7, admin_user, db)
        check(
            "工单趋势",
            len(body["data"]["dates"]) == 7
            and len(body["data"]["created"]) == 7
            and len(body["data"]["finished"]) == 7,
            str(body["data"]["dates"]),
        )

        body = stats_api.type_distribution(admin_user, db)
        check(
            "类型与状态分布",
            len(body["data"]["types"]) >= 2 and len(body["data"]["statuses"]) >= 2,
            str(len(body["data"]["types"])),
        )

        body = stats_api.toilet_ranking(5, admin_user, db)
        check(
            "厕所排行",
            len(body["data"]) == 5
            and body["data"][0]["avg_score"] >= body["data"][-1]["avg_score"],
            str(len(body["data"])),
        )

        body = stats_api.staff_ranking(5, admin_user, db)
        check(
            "员工绩效排行",
            len(body["data"]) <= 5
            and body["data"][0]["done_count"] >= body["data"][-1]["done_count"],
            str(len(body["data"])),
        )

        body = stats_api.building_heat(admin_user, db)
        check(
            "楼栋工单热力",
            len(body["data"]) >= 3 and all(item["order_count"] >= 0 for item in body["data"]),
            str(len(body["data"])),
        )

        body = stats_api.evaluation_summary(admin_user, db)
        check("评价星级分布", len(body["data"]["distribution"]) == 5, str(body["data"]["total"]))

        csv_text = stats_service.export_orders(db)
        check(
            "工单明细导出",
            csv_text.startswith("工单号,") and len(csv_text.splitlines()) >= 2,
            str(len(csv_text.splitlines())),
        )

        stale_staff = db.scalar(select(Staff).where(Staff.staff_no == "ST-TEST"))
        if stale_staff is not None:
            db.execute(delete(Staff).where(Staff.id == stale_staff.id))
        db.execute(delete(User).where(User.username == "staff_test_01"))
        db.commit()

        body = staffs_api.create_staff(
            StaffCreateIn(
                staff_no="ST-TEST",
                name="测试员工",
                phone="13800009999",
                work_type="cleaner",
                area="E栋",
                username="staff_test_01",
            ),
            admin_user,
            db,
        )
        test_staff_id = body["data"]["id"]
        check(
            "新增员工",
            body["code"] == 0 and body["data"]["account"] == "staff_test_01",
            body["msg"],
        )

        code, msg = biz_code(lambda: staffs_api.create_staff(
            StaffCreateIn(staff_no="ST-TEST", name="重复员工", phone="13800009998"), admin_user, db
        ))
        check("重复工号拦截", code == 2003, msg)

        body = staffs_api.list_staffs(
            keyword="测试员工", work_type=None, status=None, page=1, size=10, user=admin_user, db=db
        )
        check("员工列表筛选", body["data"]["total"] == 1, str(body["data"]["total"]))

        body = staffs_api.update_staff(
            test_staff_id, StaffUpdateIn(area="E栋,F栋", max_daily_orders=30), admin_user, db
        )
        check("编辑员工", body["data"]["area"] == "E栋,F栋" and body["data"]["max_daily_orders"] == 30, body["msg"])

        body = staffs_api.toggle_staff_status(test_staff_id, admin_user, db)
        check("员工上下岗", body["data"]["status"] == "off", body["data"]["status"])

        body = auth.login(LoginIn(username="staff_test_01", password="123456"), db)
        check(
            "员工账号可登录",
            body["code"] == 0 and body["data"]["user"]["role"] == "staff",
            body["msg"],
        )

        code, msg = biz_code(lambda: staffs_api.delete_staff(staff.id, admin_user, db))
        check("有关联员工不可删除", code == 2002, msg)

        body = staffs_api.delete_staff(test_staff_id, admin_user, db)
        check("删除员工", body["code"] == 0, body["msg"])

        db.execute(delete(User).where(User.username == "staff_test_01"))
        db.commit()

        body = ai_api.chat(ChatIn(message="我的工单进度怎么样了"), student, db)
        check(
            "AI 学生查询进度",
            body["code"] == 0 and "工单" in body["data"]["answer"] and bool(body["data"]["actions"]),
            body["data"]["answer"][:40],
        )

        body = ai_api.chat(ChatIn(message="厕所堵了，水都下不去"), student, db)
        check(
            "AI 通厕引导",
            any("type=unclog" in action["path"] for action in body["data"]["actions"]),
            str(body["data"]["actions"]),
        )

        body = ai_api.chat(ChatIn(message="附近哪有厕所"), student, db)
        check("AI 附近推荐", "栋" in body["data"]["answer"], body["data"]["answer"][:40])

        body = ai_api.chat(ChatIn(message="积分怎么获得"), student, db)
        check("AI 积分问答", "提交工单" in body["data"]["answer"], body["data"]["answer"][:40])

        body = ai_api.chat(ChatIn(message="有哪些超时预警"), admin_user, db)
        check("AI 管理超时洞察", "超时" in body["data"]["answer"], body["data"]["answer"][:40])

        body = ai_api.chat(ChatIn(message="现在有多少待派单"), admin_user, db)
        check(
            "AI 管理待派问答",
            "待派" in body["data"]["answer"] and body["data"]["scene"] == "admin",
            body["data"]["answer"][:40],
        )

        body = ai_api.chat(ChatIn(message="员工绩效怎么样"), admin_user, db)
        check("AI 管理绩效问答", "完成" in body["data"]["answer"], body["data"]["answer"][:40])

        result = ai_service.describe_problem("3楼厕所堵了，水都漫出来了")
        check(
            "AI 描述润色-通厕",
            result["type"] == "unclog" and result["priority"] == "urgent",
            result["type"],
        )
        result = ai_service.describe_problem("洗手台很脏，有异味")
        check("AI 描述润色-清洁", result["type"] == "clean", result["type"])
        result = ai_service.describe_problem("冲水阀一直漏水")
        check(
            "AI 描述润色-报修",
            result["type"] == "repair" and result["priority"] in ("high", "urgent"),
            result["type"],
        )

        body = ai_api.insight(admin_user, db)
        check(
            "AI 运营洞察",
            bool(body["data"]["summary"]) and len(body["data"]["insights"]) >= 1,
            str(len(body["data"]["insights"])),
        )

        db.execute(delete(DormBinding).where(DormBinding.user_id == binder.id))
        db.execute(delete(User).where(User.username == "bind_stu_01"))
        for code_value in ("D-601", "D-602"):
            leftover = db.scalar(select(Toilet).where(Toilet.code == code_value))
            if leftover:
                db.execute(delete(Toilet).where(Toilet.id == leftover.id))
        db.commit()

        db.execute(delete(User).where(User.username == "check_stu_01"))
        db.commit()

    passed = sum(1 for _, condition, _ in results if condition)
    for name, condition, detail in results:
        print(f"[{'PASS' if condition else 'FAIL'}] {name}" + ("" if condition else f" -> {detail}"))
    print(f"\n合计 {len(results)} 项，通过 {passed} 项")
    if passed != len(results):
        raise SystemExit(1)


if __name__ == "__main__":
    main()