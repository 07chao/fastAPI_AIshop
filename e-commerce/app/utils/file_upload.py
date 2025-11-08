import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status
from fastapi.responses import JSONResponse
from typing import Optional

# 配置上传目录
UPLOAD_DIR = Path("uploads")
PRODUCT_IMAGES_DIR = UPLOAD_DIR / "products"
USER_AVATARS_DIR = UPLOAD_DIR / "avatars"

# 创建上传目录
PRODUCT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
USER_AVATARS_DIR.mkdir(parents=True, exist_ok=True)

# 允许的文件类型
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/jpg", "image/png", "image/gif", "image/webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


async def save_uploaded_file(
    file: UploadFile,
    upload_type: str = "product",  # "product" 或 "avatar"
    old_file_path: Optional[str] = None
) -> str:
    """
    保存上传的文件
    
    Args:
        file: 上传的文件
        upload_type: 上传类型 ("product" 或 "avatar")
        old_file_path: 旧文件路径（如果存在则删除）
    
    Returns:
        文件的相对URL路径
    """
    # 验证文件类型
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_IMAGE_TYPES)}"
        )
    
    # 读取文件内容
    contents = await file.read()
    
    # 验证文件大小
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_FILE_SIZE / 1024 / 1024}MB"
        )
    
    # 生成唯一文件名
    file_extension = Path(file.filename).suffix.lower()
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    
    # 确定保存目录
    if upload_type == "product":
        save_dir = PRODUCT_IMAGES_DIR
        url_prefix = "/uploads/products/"
    elif upload_type == "avatar":
        save_dir = USER_AVATARS_DIR
        url_prefix = "/uploads/avatars/"
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid upload type. Must be 'product' or 'avatar'"
        )
    
    # 保存文件
    file_path = save_dir / unique_filename
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # 删除旧文件（如果存在）
    if old_file_path:
        try:
            old_path = Path(old_file_path.replace("/uploads/", "uploads/"))
            if old_path.exists() and old_path.is_file():
                old_path.unlink()
        except Exception:
            pass  # 忽略删除旧文件时的错误
    
    # 返回文件的URL路径
    return f"{url_prefix}{unique_filename}"


async def delete_file(file_path: str) -> bool:
    """
    删除文件
    
    Args:
        file_path: 文件的URL路径
    
    Returns:
        是否成功删除
    """
    try:
        # 将URL路径转换为文件系统路径
        if file_path.startswith("/uploads/"):
            file_path = file_path[1:]  # 移除开头的 /
        
        path = Path(file_path)
        if path.exists() and path.is_file():
            path.unlink()
            return True
        return False
    except Exception:
        return False

