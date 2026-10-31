from typing import Iterator

import jwt
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import BizException
from app.core.response import BizCode
from app.core.security import decode_token
from app.db.database import SessionLocal
from app.models.user import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise BizException(BizCode.UNAUTHORIZED, "未登录或登录已过期")
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload.get("sub", 0))
    except (jwt.PyJWTError, ValueError, TypeError):
        raise BizException(BizCode.UNAUTHORIZED, "登录凭证无效，请重新登录")
    user = db.get(User, user_id)
    if user is None:
        raise BizException(BizCode.UNAUTHORIZED, "用户不存在，请重新登录")
    if user.status != 1:
        raise BizException(BizCode.FORBIDDEN, "账号已被禁用，请联系管理员")
    return user


def require_role(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise BizException(BizCode.FORBIDDEN, "当前角色无权限执行该操作")
        return user

    return checker