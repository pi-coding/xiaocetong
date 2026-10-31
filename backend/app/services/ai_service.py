import json
import re
import urllib.request
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Evaluation, ServiceOrder, Toilet, User
from app.services import alert_service, order_service, stats_service, toilet_service

SYSTEM_PROMPT = (
    "你是「校厕通」校园厕所智能管家助手，面向学生和后勤管理员。"
    "回答要简短、具体、可执行，使用简体中文，不超过 200 字。"
    "涉及提交工单、查看进度、超时预警等操作时，给出明确建议。"
)

TYPE_KEYWORDS = {
    "unclog": ["堵", "反水", "不下水", "冲不下", "溢", "水位", "臭味重"],
    "clean": ["脏", "臭", "垃圾", "水渍", "污渍", "积垢", "异味", "纸屑"],
    "repair": ["坏", "漏", "锁", "灯", "龙头", "阀", "门", "不出水", "松动", "破损", "不亮"],
}

URGENT_KEYWORDS = ["溢出", "漫出", "流出来", "没法用", "完全堵", "大面积", "满地", "无法关闭"]
HIGH_KEYWORDS = ["堵", "漏水", "长时间", "几天", "严重"]

TYPE_LABEL = {"unclog": "通厕所", "clean": "清洁", "repair": "报修"}


def _hit(text: str, keywords: list[str]) -> bool:
    return any(word in text for word in keywords)


def _actions(*items: tuple[str, str]) -> list[dict]:
    return [{"label": label, "path": path} for label, path in items]


def _recent_orders(db: Session, user: User, limit: int = 3) -> list[ServiceOrder]:
    return list(
        db.scalars(
            select(ServiceOrder)
            .where(ServiceOrder.user_id == user.id)
            .order_by(ServiceOrder.created_at.desc())
            .limit(limit)
        ).all()
    )


def _student_reply(db: Session, user: User, message: str) -> dict:
    text = message.strip()

    if _hit(text, ["进度", "到哪", "处理", "状态", "催单", "我的工单", "看一眼"]):
        orders = _recent_orders(db, user)
        if not orders:
            return {
                "answer": "你还没有提交过工单。如果厕所堵塞、脏乱或设施损坏，可以直接在「工单」里提交，系统会按紧急程度安排处理。",
                "actions": _actions(("去提交工单", "/student/orders/create")),
            }
        lines = [
            f"· {item.order_no}（{order_service.TYPE_TEXT.get(item.type, item.type)}）"
            f"{order_service.STATUS_TEXT.get(item.status, item.status)}，"
            f"提交于 {item.created_at:%m-%d %H:%M}"
            for item in orders
        ]
        return {
            "answer": "你最近的工单：\n" + "\n".join(lines) + "\n需要催单可在工单详情页操作。",
            "actions": _actions(("查看全部工单", "/student/orders")),
        }

    if _hit(text, ["堵", "反水", "不下水", "冲不下", "溢"]):
        return {
            "answer": "这属于「通厕所」问题。建议立即提交工单并选择高优先级，注明具体隔间位置；如果是满溢或完全无法使用，请选紧急，响应时限会缩短到 2 小时。",
            "actions": _actions(
                ("提交通厕工单", "/student/orders/create?type=unclog"),
                ("查看我的工单", "/student/orders"),
            ),
        }

    if _hit(text, ["脏", "臭", "垃圾", "清洁", "异味"]):
        return {
            "answer": "这属于「清洁」问题。提交工单时建议上传现场照片并勾选普通优先级，保洁完成打卡后清洁时间会自动刷新。",
            "actions": _actions(("提交清洁工单", "/student/orders/create?type=clean")),
        }

    if _hit(text, ["坏", "漏水", "锁", "灯", "龙头", "修"]):
        return {
            "answer": "这属于「报修」问题。请描述损坏部位并上传照片，系统会优先派给维修工。若影响整层使用，请选择高优先级。",
            "actions": _actions(("提交报修工单", "/student/orders/create?type=repair")),
        }

    if _hit(text, ["厕所", "在哪", "位置", "最近", "哪边"]):
        nearby = toilet_service.nearby_toilets(db, user, 3)
        if not nearby:
            return {
                "answer": "暂时没有可推荐的公共厕所，可以到「找厕所」页面查看全部。",
                "actions": _actions(("打开找厕所", "/student/toilets")),
            }
        lines = [
            f"· {item['name']}（{item['building']} 栋 {item['floor']} 层，{item['status_text']}）"
            for item in nearby
        ]
        return {
            "answer": "离你较近的公共厕所：\n" + "\n".join(lines) + "\n点击可查看清洁状态和详情。",
            "actions": _actions(("查看厕所列表", "/student/toilets")),
        }

    if "积分" in text:
        return {
            "answer": "积分规则：提交工单 +5，工单完成 +10，完成服务评价 +5，每日签到 +2。积分可在「我的」-「我的积分」查看明细与排行榜。",
            "actions": _actions(("查看我的积分", "/student/points")),
        }

    if _hit(text, ["多久", "周期", "标准", "打扫"]):
        return {
            "answer": "公共厕所的清洁周期默认 4 小时，宿舍厕所 24 小时。超过周期未清洁会自动进入预警列表，管理员可一键生成清洁工单。",
            "actions": _actions(("查看厕所清洁状态", "/student/toilets")),
        }

    if _hit(text, ["投诉", "建议", "意见", "谢谢"]):
        return {
            "answer": "已记录你的反馈。如涉及具体厕所，建议同时提交工单并上传照片，管理员会在「评价管理」中跟进处理。",
            "actions": _actions(("提交工单", "/student/orders/create")),
        }

    return {
        "answer": "我可以帮你：1）查询工单进度；2）引导提交通厕/清洁/报修工单；3）推荐附近厕所；4）说明积分与清洁规则。直接问我即可。",
        "actions": _actions(
            ("提交工单", "/student/orders/create"),
            ("查看我的工单", "/student/orders"),
            ("找厕所", "/student/toilets"),
        ),
    }


def _admin_reply(db: Session, message: str) -> dict:
    text = message.strip()

    if _hit(text, ["超时", "预警", "未打扫", "没打扫", "打扫"]):
        items = alert_service.overdue_toilets(db)[:3]
        if not items:
            return {
                "answer": "当前没有超时未打扫的公共厕所，清洁状态整体正常。",
                "actions": _actions(("打开预警中心", "/admin/alerts")),
            }
        lines = [
            f"· {item['name']}（{item['building']} 栋）超时 "
            f"{'暂无记录' if item['never_cleaned'] else str(item['overdue_minutes']) + ' 分钟'}，"
            f"等级：{item['level_text']}"
            for item in items
        ]
        return {
            "answer": f"当前有 {len(alert_service.overdue_toilets(db))} 间厕所超时未打扫，最严重的几间：\n"
            + "\n".join(lines)
            + "\n可一键生成清洁工单后去 AI 派单。",
            "actions": _actions(("打开预警中心", "/admin/alerts"), ("去 AI 派单", "/admin/dispatch")),
        }

    if _hit(text, ["待派", "派单", "没人管", "积压"]):
        pending = stats_service.overview(db)["pending_orders"]
        if pending == 0:
            return {
                "answer": "当前没有待派单工单，处置链路正常。",
                "actions": _actions(("打开工单看板", "/admin/orders")),
            }
        return {
            "answer": f"当前有 {pending} 张工单待派单。建议使用 AI 派单，按区域、负载、时效与评分综合推荐处理人。",
            "actions": _actions(("去 AI 派单", "/admin/dispatch"), ("打开工单看板", "/admin/orders")),
        }

    if _hit(text, ["员工", "绩效", "谁最", "保洁"]):
        staff = stats_service.staff_ranking(db, 3)
        if not staff:
            return {
                "answer": "暂无员工绩效数据。",
                "actions": _actions(("员工管理", "/admin/staffs")),
            }
        lines = [
            f"· {item['name']}：完成 {item['done_count']} 单，平均 {item['avg_duration_min']} 分钟，"
            f"评分 {item['avg_score']:.1f}"
            for item in staff
        ]
        return {
            "answer": "当前绩效前三：\n" + "\n".join(lines) + "\n可结合负载情况调整派单。",
            "actions": _actions(("员工管理", "/admin/staffs"), ("统计报表", "/admin/stats")),
        }

    if _hit(text, ["差评", "评价", "投诉", "不满意"]):
        rows = list(
            db.scalars(
                select(Evaluation)
                .where(Evaluation.score <= 3)
                .order_by(Evaluation.created_at.desc())
                .limit(3)
            ).all()
        )
        if not rows:
            return {
                "answer": "近期没有 3 星及以下的差评，服务质量稳定。",
                "actions": _actions(("评价管理", "/admin/evaluations")),
            }
        return {
            "answer": f"近期有 {len(rows)} 条低分评价，建议逐条回复并复盘。可在评价管理中筛选差评处理。",
            "actions": _actions(("评价管理", "/admin/evaluations")),
        }

    if _hit(text, ["统计", "报表", "本周", "数据", "情况", "多少"]):
        ov = stats_service.overview(db)
        return {
            "answer": (
                f"今日新增 {ov['today_orders']} 单、完成 {ov['today_done']} 单；"
                f"待派 {ov['pending_orders']} 单，超时 {ov['overdue_orders']} 单；"
                f"超时未打扫 {ov['overdue_toilets']} 间；满意度 {ov['avg_rating']} 分。"
            ),
            "actions": _actions(("查看统计报表", "/admin/stats"), ("数据驾驶舱", "/admin/dashboard")),
        }

    if _hit(text, ["厕所", "台账", "数量"]):
        ov = stats_service.overview(db)
        return {
            "answer": f"当前共 {ov['toilet_total']} 间厕所（公共 {ov['public_total']}、宿舍 {ov['dorm_total']}），平均评分 {ov['avg_toilet_score']}。",
            "actions": _actions(("公共厕所台账", "/admin/toilets")),
        }

    ov = stats_service.overview(db)
    return {
        "answer": (
            f"今日新增 {ov['today_orders']} 单、完成 {ov['today_done']} 单，"
            f"待派 {ov['pending_orders']} 单、超时 {ov['overdue_orders']} 单，"
            f"超时厕所 {ov['overdue_toilets']} 间。可以问我「超时预警」「待派单」「员工绩效」「统计数据」。"
        ),
        "actions": _actions(("数据驾驶舱", "/admin/dashboard"), ("统计报表", "/admin/stats")),
    }


def _llm_answer(message: str, scene: str, context: str) -> Optional[str]:
    if not settings.ai_api_key:
        return None
    payload = {
        "model": settings.ai_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"当前场景：{scene}\n实时数据：{context}\n用户问题：{message}"},
        ],
        "temperature": 0.3,
        "max_tokens": 500,
    }
    request = urllib.request.Request(
        f"{settings.ai_base_url.rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {settings.ai_api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=8) as response:
        data = json.loads(response.read().decode("utf-8"))
    content = data["choices"][0]["message"]["content"]
    return str(content).strip() or None


def chat(db: Session, user: User, message: str, scene: str) -> dict:
    scene = scene if scene in ("student", "admin") else ("admin" if user.role == "admin" else "student")
    rule = _student_reply(db, user, message) if scene == "student" else _admin_reply(db, message)

    context = (rule.get("answer") or "")[:400]
    try:
        answer = _llm_answer(message, scene, context)
    except Exception:
        answer = None

    return {
        "answer": answer or rule["answer"],
        "actions": rule.get("actions", []),
        "source": "llm" if answer else "rule",
        "scene": scene,
    }


def describe_problem(text: str) -> dict:
    cleaned = re.sub(r"\s+", " ", text).strip()
    order_type = "clean"
    for candidate, keywords in TYPE_KEYWORDS.items():
        if _hit(cleaned, keywords):
            order_type = candidate
            break

    priority = "normal"
    if _hit(cleaned, URGENT_KEYWORDS):
        priority = "urgent"
    elif _hit(cleaned, HIGH_KEYWORDS):
        priority = "high"

    snippet = cleaned[:24]
    prefix = {"unclog": "蹲位堵塞", "clean": "清洁诉求", "repair": "设施报修"}[order_type]
    title = f"{prefix}：{snippet}"[:64]

    description = cleaned
    if order_type == "unclog":
        description += "。请尽快安排疏通，避免影响正常使用。"
    elif order_type == "clean":
        description += "。请安排保洁处理并补充耗材。"
    else:
        description += "。请安排维修人员到场处理。"

    suggestions = ["上传现场照片，便于快速判断", "填写具体楼层与隔间位置"]
    if priority == "urgent":
        suggestions.append("已识别为紧急问题，响应时限 2 小时")

    return {
        "type": order_type,
        "type_text": TYPE_LABEL[order_type],
        "title": title,
        "description": description[:1000],
        "priority": priority,
        "suggestions": suggestions,
    }


def build_insight(db: Session) -> dict:
    ov = stats_service.overview(db)
    alerts = alert_service.overdue_toilets(db)
    heat = stats_service.building_heat(db)
    staff = stats_service.staff_ranking(db, 3)

    insights = []
    if alerts:
        worst = alerts[0]
        insights.append(
            {
                "level": "danger" if worst["warn_level"] >= 2 else "warning",
                "title": "超时未打扫",
                "detail": (
                    f"{worst['name']} 已超时 {worst['overdue_minutes']} 分钟（{worst['level_text']}），"
                    f"责任保洁：{worst['cleaner_name'] or '未指派'}。"
                ),
                "path": "/admin/alerts",
            }
        )
    if ov["pending_orders"]:
        insights.append(
            {
                "level": "warning",
                "title": "待派单积压",
                "detail": f"当前 {ov['pending_orders']} 张工单待派单，建议使用 AI 批量派单缩短响应时间。",
                "path": "/admin/dispatch",
            }
        )
    if ov["evaluation_count"] and ov["avg_rating"] < 4.5:
        insights.append(
            {
                "level": "warning",
                "title": "满意度需关注",
                "detail": f"当前平均评价 {ov['avg_rating']} 分，低于 4.5，建议查看差评并回复。",
                "path": "/admin/evaluations",
            }
        )
    if heat:
        top_building = max(heat, key=lambda item: item["order_count"])
        if top_building["order_count"]:
            insights.append(
                {
                    "level": "info",
                    "title": "楼栋工单集中",
                    "detail": (
                        f"{top_building['building']} 栋工单量最高（{top_building['order_count']} 单，"
                        f"超时 {top_building['timeout_count']} 单），建议增加巡检频次。"
                    ),
                    "path": "/admin/stats",
                }
            )
    if staff:
        top = staff[0]
        insights.append(
            {
                "level": "success",
                "title": "绩效标杆",
                "detail": (
                    f"{top['name']} 已完成 {top['done_count']} 单，平均 {top['avg_duration_min']} 分钟，"
                    f"评分 {top['avg_score']:.1f}，可作为派单优先人选。"
                ),
                "path": "/admin/staffs",
            }
        )

    summary = (
        f"今日新增 {ov['today_orders']} 单、完成 {ov['today_done']} 单；"
        f"待派 {ov['pending_orders']} 单、超时 {ov['overdue_orders']} 单；"
        f"超时未打扫 {ov['overdue_toilets']} 间，满意度 {ov['avg_rating']} 分。"
    )
    return {
        "summary": summary,
        "insights": insights,
        "generated_at": datetime.now(),
        "source": "rule",
    }