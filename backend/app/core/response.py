from typing import Any


class BizCode:
    OK = 0
    PARAM_ERROR = 1000
    UNAUTHORIZED = 1001
    FORBIDDEN = 1002
    NOT_FOUND = 2001
    STATE_ERROR = 2002
    DUPLICATE = 2003
    THIRD_PARTY = 3001
    SERVER_ERROR = 5000


def ok(data: Any = None, msg: str = "ok") -> dict:
    return {"code": BizCode.OK, "msg": msg, "data": data}


def fail(code: int = BizCode.STATE_ERROR, msg: str = "操作失败", data: Any = None) -> dict:
    return {"code": code, "msg": msg, "data": data}


def page_data(items: list, total: int, page: int, size: int) -> dict:
    pages = (total + size - 1) // size if size else 0
    return {"list": items, "total": total, "page": page, "size": size, "pages": pages}