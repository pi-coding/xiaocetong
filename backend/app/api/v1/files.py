from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.exceptions import BizException
from app.core.response import BizCode, ok

router = APIRouter(prefix="/files", tags=["文件"])

MAX_SIZE = 5 * 1024 * 1024
CONTENT_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
}


@router.post("/upload", summary="上传图片")
def upload_image(
    file: UploadFile = File(...),
    user=Depends(get_current_user),
):
    suffix = CONTENT_EXT.get(file.content_type or "")
    if suffix is None:
        raise BizException(BizCode.PARAM_ERROR, "仅支持 jpg、png、webp、gif 图片")

    data = file.file.read(MAX_SIZE + 1)
    if not data:
        raise BizException(BizCode.PARAM_ERROR, "上传文件为空")
    if len(data) > MAX_SIZE:
        raise BizException(BizCode.PARAM_ERROR, "图片不能超过 5MB")

    directory = Path(settings.upload_dir)
    directory.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{suffix}"
    (directory / filename).write_bytes(data)

    return ok(
        {
            "url": f"/uploads/{filename}",
            "filename": file.filename,
            "size": len(data),
        },
        "上传成功",
    )