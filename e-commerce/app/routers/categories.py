from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.database.session import get_db
from app.utils.token import get_current_user, get_current_admin
from app.services.category_service import CategoryService
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse


router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=list[CategoryResponse])
async def get_all_categories(
        include_inactive: bool = Query(False, description="是否包含未启用的分类"),
        db: AsyncSession = Depends(get_db)):
  """获取所有分类（树形结构）"""
  try:
    categories = await CategoryService.get_all_categories(db, include_inactive)
    return categories
  except HTTPException as exc:
    return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category_by_id(
        category_id: int,
        db: AsyncSession = Depends(get_db)):
  """根据ID获取分类"""
  try:
    category = await CategoryService.get_category_by_id(db, category_id)
    return category
  except HTTPException as exc:
    return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
        category_data: CategoryCreate,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_admin)):
  """创建分类（仅管理员）"""
  try:
    category = await CategoryService.create_category(db, category_data)
    return category
  except HTTPException as exc:
    return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
        category_id: int,
        category_data: CategoryUpdate,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_admin)):
  """更新分类（仅管理员）"""
  try:
    category = await CategoryService.update_category(db, category_id, category_data)
    return category
  except HTTPException as exc:
    return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)


@router.delete("/{category_id}")
async def delete_category(
        category_id: int,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_admin)):
  """删除分类（仅管理员）"""
  try:
    result = await CategoryService.delete_category(db, category_id)
    return result
  except HTTPException as exc:
    return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

