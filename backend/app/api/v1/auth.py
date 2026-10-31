from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.exceptions import BizException
from app.core.response import BizCode, ok
from app.core.security import create_token, hash_password, verify_password
from app.core.config import settings
from app.models.user import User
from app.schemas.user import (
    LoginIn,
    PasswordChangeIn,
    ProfileUpdateIn,
    RegisterIn,
    TokenOut,
    UserOut,
)

router = APIRouter(prefix="/auth", tags=["认证"])


def _user_out(user: User) -> dict:
    return UserOut.model_validate(user).model_dump(mode="json")


@router.post("/register", summary="学生注册")
def register(payload: RegisterIn, db: Session = Depends(get_db)):
    exists = db.scalar(select(User).where(User.username == payload.username))
    if exists:
        raise BizException(BizCode.DUPLICATE, "用户名已存在")
    if payload.student_no:
        dup_no = db.scalar(select(User).where(User.student_no == payload.student_no))
        if dup_no:
            raise BizException(BizCode.DUPLICATE, "学号已被注册")
    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        real_name=payload.real_name,
        role="student",
        phone=payload.phone,
        student_no=payload.student_no or payload.username,
        building=payload.building,
        room_no=payload.room_no,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ok(_user_out(user), "注册成功")


@router.post("/login", summary="登录")
def login(payload: LoginIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.username == payload.username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise BizException(BizCode.UNAUTHORIZED, "用户名或密码错误")
    if user.status != 1:
        raise BizException(BizCode.FORBIDDEN, "账号已被禁用，请联系管理员")
    user.last_login_at = datetime.now()
    db.commit()
    db.refresh(user)
    token = create_token(user.id, user.role)
    data = TokenOut(
        token=token,
        expires_in=settings.jwt_expire_minutes * 60,
        user=UserOut.model_validate(user),
    ).model_dump(mode="json")
    return ok(data, "登录成功")


@router.get("/me", summary="当前用户信息")
def me(user: User = Depends(get_current_user)):
    return ok(_user_out(user))


@router.put("/me", summary="修改个人资料")
def update_me(
    payload: ProfileUpdateIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    changes = payload.model_dump(exclude_unset=True)
    if changes.get("real_name") is None:
        changes.pop("real_name", None)
    for field, value in changes.items():
        setattr(user, field, value)
    db.commit()
    db.refresh(user)
    return ok(_user_out(user), "资料已更新")


@router.put("/password", summary="修改密码")
def change_password(
    payload: PasswordChangeIn,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not verify_password(payload.old_password, user.password_hash):
        raise BizException(BizCode.PARAM_ERROR, "原密码不正确")
    if payload.old_password == payload.new_password:
        raise BizException(BizCode.PARAM_ERROR, "新密码不能与原密码相同")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return ok(None, "密码修改成功")