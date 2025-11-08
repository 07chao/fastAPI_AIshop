from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from typing import Optional

from sqlalchemy.future import select
from app.database.session import get_db
from app.utils.token import get_current_user
from app.utils.file_upload import save_uploaded_file, delete_file
from app.models.product import Product
from app.models.user import User
from app.schemas.user import Role


router = APIRouter(prefix="/uploads", tags=["File Uploads"])


@router.post("/product-image/{product_id}")
async def upload_product_image(
        product_id: int,
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user)):
  """
  上传商品图片
  只有商品的所有者（商家）或管理员可以上传
  """
  try:
    # 验证权限：获取商品信息
    product_query = await db.execute(
      select(Product).where(Product.id == product_id)
    )
    product = product_query.scalars().first()
    
    if not product:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Product not found"
      )
    
    # 检查权限
    if current_user.role != Role.admin and product.vendor_id != current_user.id:
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You do not have permission to upload image for this product"
      )
    
    # 保存文件
    image_url = await save_uploaded_file(
      file,
      upload_type="product",
      old_file_path=product.image_url
    )
    
    # 更新商品图片URL
    product.image_url = image_url
    await db.commit()
    await db.refresh(product)
    
    return {
      "message": "Product image uploaded successfully",
      "image_url": image_url,
      "product_id": product_id
    }
  except HTTPException as exc:
    return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)


@router.post("/avatar")
async def upload_user_avatar(
        file: UploadFile = File(...),
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user)):
  """
  上传用户头像
  用户只能上传自己的头像
  """
  try:
    # 获取用户信息
    user_query = await db.execute(
      select(User).where(User.id == current_user.id)
    )
    user = user_query.scalars().first()
    
    if not user:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="User not found"
      )
    
    # 保存文件
    image_url = await save_uploaded_file(
      file,
      upload_type="avatar",
      old_file_path=user.image_url
    )
    
    # 更新用户头像URL
    user.image_url = image_url
    await db.commit()
    await db.refresh(user)
    
    return {
      "message": "Avatar uploaded successfully",
      "image_url": image_url,
      "user_id": user.id
    }
  except HTTPException as exc:
    return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

