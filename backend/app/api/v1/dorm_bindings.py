from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_role
from app.core.exceptions import BizException
from app.core.response import BizCode, ok
from app.models import DormBinding, Toilet
from app.schemas.dorm_binding import (
    BindingCreateIn,
    BindingMatchOut,
    BindingOut,
    BindingUpdateIn,
)
from app.schemas.toilet import ToiletOut
from app.services import toilet_service as svc

router = APIRouter(prefix="/dorm-bindings", tags=["宿舍绑定"])


def _active_binding(db: Session, user_id: int, exclude_id: int | None = None) -> DormBinding | None:
    stmt = select(DormBinding).where(DormBinding.user_id == user_id, DormBinding.status == 1)
    if exclude_id:
        stmt = stmt.where(DormBinding.id != exclude_id)
    return db.scalar(stmt)


def _binding_dict(db: Session, binding: DormBinding) -> dict:
    toilet = db.get(Toilet, binding.toilet_id)
    data = {
        "id": binding.id,
        "user_id": binding.user_id,
        "toilet_id": binding.toilet_id,
        "building": binding.building,
        "floor": binding.floor,
        "room_no": binding.room_no,
        "bind_type": binding.bind_type,
        "status": binding.status,
        "toilet": None,
    }
    if toilet is not None:
        data["toilet"] = ToiletOut(**svc.to_dicts(db, [toilet])[0]).model_dump(mode="json")
    return BindingOut(**data).model_dump(mode="json")


def _ensure_owned(binding: DormBinding, user) -> None:
    if binding.user_id != user.id:
        raise BizException(BizCode.FORBIDDEN, "只能操作自己的宿舍绑定")


@router.get("/my", summary="我的宿舍厕所绑定")
def my_binding(user=Depends(require_role("student")), db: Session = Depends(get_db)):
    binding = _active_binding(db, user.id)
    if binding is None:
        return ok(None, "尚未绑定宿舍厕所")
    return ok(_binding_dict(db, binding))


@router.get("/match", summary="按宿舍匹配厕所")
def match_binding(
    building: str = Query(min_length=1, max_length=32),
    room_no: str = Query(min_length=1, max_length=16),
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    build = building.strip().upper()
    room = room_no.strip()
    toilet = svc.find_dorm_toilet(db, build, room)
    code = f"{build}-{room}".upper()
    data = BindingMatchOut(
        code=code,
        exists=toilet is not None,
        toilet=ToiletOut(**svc.to_dicts(db, [toilet])[0]) if toilet else None,
    ).model_dump(mode="json")
    return ok(data)


@router.post("", summary="绑定宿舍厕所")
def create_binding(
    payload: BindingCreateIn,
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    if _active_binding(db, user.id):
        raise BizException(BizCode.DUPLICATE, "你已绑定宿舍厕所，如需更换请使用换绑")

    toilet = svc.find_or_create_dorm_toilet(db, payload.building, payload.room_no, payload.floor)
    binding = DormBinding(
        user_id=user.id,
        toilet_id=toilet.id,
        building=toilet.building,
        floor=toilet.floor,
        room_no=payload.room_no.strip(),
        bind_type=payload.bind_type,
        status=1,
    )
    db.add(binding)
    user.building = toilet.building
    user.room_no = payload.room_no.strip()
    db.commit()
    db.refresh(binding)
    return ok(_binding_dict(db, binding), "绑定成功")


@router.put("/{binding_id}", summary="换绑宿舍厕所")
def update_binding(
    binding_id: int,
    payload: BindingUpdateIn,
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    binding = db.get(DormBinding, binding_id)
    if binding is None:
        raise BizException(BizCode.NOT_FOUND, "绑定记录不存在")
    _ensure_owned(binding, user)
    if binding.status != 1:
        raise BizException(BizCode.STATE_ERROR, "该绑定已失效，请重新绑定")

    duplicate = _active_binding(db, user.id, exclude_id=binding.id)
    if duplicate is not None:
        raise BizException(BizCode.DUPLICATE, "存在其他有效绑定，请先解绑")

    toilet = svc.find_or_create_dorm_toilet(db, payload.building, payload.room_no, payload.floor)
    binding.toilet_id = toilet.id
    binding.building = toilet.building
    binding.floor = toilet.floor
    binding.room_no = payload.room_no.strip()
    binding.bind_type = payload.bind_type
    user.building = toilet.building
    user.room_no = payload.room_no.strip()
    db.commit()
    db.refresh(binding)
    return ok(_binding_dict(db, binding), "换绑成功")


@router.delete("/{binding_id}", summary="解绑宿舍厕所")
def delete_binding(
    binding_id: int,
    user=Depends(require_role("student")),
    db: Session = Depends(get_db),
):
    binding = db.get(DormBinding, binding_id)
    if binding is None:
        raise BizException(BizCode.NOT_FOUND, "绑定记录不存在")
    _ensure_owned(binding, user)
    binding.status = 0
    db.commit()
    return ok(None, "解绑成功")