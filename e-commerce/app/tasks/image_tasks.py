"""
图片处理异步任务
"""
from app.celery_app import celery_app
from PIL import Image
import os
from pathlib import Path


@celery_app.task(name="process_product_image")
def process_product_image(image_path: str, output_dir: str = "uploads/products/processed"):
    """
    异步处理商品图片（缩略图、压缩等）
    
    Args:
        image_path: 原始图片路径
        output_dir: 输出目录
    
    Returns:
        str: 处理后的图片路径
    """
    try:
        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 打开图片
        img = Image.open(image_path)
        
        # 生成缩略图（300x300）
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        
        # 保存缩略图
        filename = Path(image_path).stem
        thumbnail_path = os.path.join(output_dir, f"{filename}_thumb.jpg")
        img.save(thumbnail_path, "JPEG", quality=85, optimize=True)
        
        return thumbnail_path
    except Exception as e:
        print(f"Failed to process product image {image_path}: {e}")
        raise


@celery_app.task(name="process_user_avatar")
def process_user_avatar(image_path: str, output_dir: str = "uploads/avatars/processed"):
    """
    异步处理用户头像（圆形裁剪、压缩等）
    
    Args:
        image_path: 原始图片路径
        output_dir: 输出目录
    
    Returns:
        str: 处理后的图片路径
    """
    try:
        # 创建输出目录
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # 打开图片
        img = Image.open(image_path)
        
        # 转换为正方形（取最小边）
        size = min(img.size)
        img = img.crop((0, 0, size, size))
        
        # 调整大小为200x200
        img = img.resize((200, 200), Image.Resampling.LANCZOS)
        
        # 保存处理后的头像
        filename = Path(image_path).stem
        processed_path = os.path.join(output_dir, f"{filename}_processed.jpg")
        img.save(processed_path, "JPEG", quality=90, optimize=True)
        
        return processed_path
    except Exception as e:
        print(f"Failed to process user avatar {image_path}: {e}")
        raise

