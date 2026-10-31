import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.db.base import Base
from app.db.database import engine
from app import models as _models  # noqa: F401

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    logging.getLogger("cct").info("%s 启动完成，数据库已就绪", settings.app_name)
    yield


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="校园厕所智能管家：学生报单、AI 派单、超时预警、统计报表",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(api_router, prefix=settings.api_prefix)

Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.get("/", tags=["系统"], summary="服务信息")
def root():
    return {
        "code": 0,
        "msg": "ok",
        "data": {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "api": settings.api_prefix,
        },
    }