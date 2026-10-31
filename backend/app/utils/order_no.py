from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ServiceOrder


def gen_order_no(db: Session) -> str:
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"WC{today}"
    last = db.scalar(
        select(ServiceOrder.order_no)
        .where(ServiceOrder.order_no.like(f"{prefix}%"))
        .order_by(ServiceOrder.order_no.desc())
        .limit(1)
    )
    seq = int(last[-4:]) + 1 if last and last[-4:].isdigit() else 1
    return f"{prefix}{seq:04d}"