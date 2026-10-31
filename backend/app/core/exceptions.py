import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.response import BizCode, fail

logger = logging.getLogger("cct")


class BizException(Exception):
    def __init__(self, code: int = BizCode.STATE_ERROR, msg: str = "操作失败", data: Any = None):
        self.code = code
        self.msg = msg
        self.data = data
        super().__init__(msg)


def _json(code: int, msg: str, data: Any = None) -> JSONResponse:
    return JSONResponse(status_code=200, content=fail(code, msg, data))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(BizException)
    async def _biz(request: Request, exc: BizException):
        return _json(exc.code, exc.msg, exc.data)

    @app.exception_handler(RequestValidationError)
    async def _validation(request: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(i) for i in first.get("loc", []) if i not in ("body", "query", "path"))
        msg = first.get("msg", "参数错误")
        return _json(BizCode.PARAM_ERROR, f"参数错误：{loc} {msg}", first.get("input"))

    @app.exception_handler(StarletteHTTPException)
    async def _http(request: Request, exc: StarletteHTTPException):
        mapping = {401: BizCode.UNAUTHORIZED, 403: BizCode.FORBIDDEN, 404: BizCode.NOT_FOUND}
        return _json(mapping.get(exc.status_code, BizCode.STATE_ERROR), str(exc.detail))

    @app.exception_handler(Exception)
    async def _server(request: Request, exc: Exception):
        logger.exception("unhandled error: %s %s", request.method, request.url.path)
        return _json(BizCode.SERVER_ERROR, "服务器内部错误")