from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.category import Category
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse


class CategoryService:
  @staticmethod
  async def get_all_categories(db: AsyncSession, include_inactive: bool = False):
    """获取所有分类（树形结构）"""
    query = select(Category)
    if not include_inactive:
      query = query.where(Category.is_active == True)
    query = query.order_by(Category.level, Category.id)
    
    result = await db.execute(query)
    all_categories = result.scalars().all()
    
    # 构建树形结构
    category_dict = {cat.id: CategoryResponse(
      id=cat.id,
      name=cat.name,
      description=cat.description,
      parent_id=cat.parent_id,
      level=cat.level,
      is_active=cat.is_active,
      created_at=cat.created_at,
      updated_at=cat.updated_at,
      children=None
    ) for cat in all_categories}
    
    # 构建父子关系
    root_categories = []
    for cat in all_categories:
      category_response = category_dict[cat.id]
      if cat.parent_id is None:
        # 一级分类
        root_categories.append(category_response)
      else:
        # 二级分类，添加到父分类的children中
        if cat.parent_id in category_dict:
          parent = category_dict[cat.parent_id]
          if parent.children is None:
            parent.children = []
          parent.children.append(category_response)
    
    return root_categories

  @staticmethod
  async def get_category_by_id(db: AsyncSession, category_id: int):
    """根据ID获取分类"""
    # 使用 selectinload 预加载子分类
    query = await db.execute(
      select(Category)
      .options(selectinload(Category.children))
      .where(Category.id == category_id)
    )
    category = query.scalars().first()
    
    if not category:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Category not found"
      )
    
    # 手动构建响应对象，避免异步加载问题
    children_list = None
    if category.children:
      children_list = [
        CategoryResponse(
          id=child.id,
          name=child.name,
          description=child.description,
          parent_id=child.parent_id,
          level=child.level,
          is_active=child.is_active,
          created_at=child.created_at,
          updated_at=child.updated_at,
          children=None  # 二级分类不再有子分类
        )
        for child in category.children
      ]
    
    return CategoryResponse(
      id=category.id,
      name=category.name,
      description=category.description,
      parent_id=category.parent_id,
      level=category.level,
      is_active=category.is_active,
      created_at=category.created_at,
      updated_at=category.updated_at,
      children=children_list
    )

  @staticmethod
  async def create_category(db: AsyncSession, category_data: CategoryCreate):
    """创建分类"""
    # 如果是二级分类，验证父分类是否存在
    if category_data.parent_id:
      parent_query = await db.execute(
        select(Category).where(Category.id == category_data.parent_id)
      )
      parent = parent_query.scalars().first()
      
      if not parent:
        raise HTTPException(
          status_code=status.HTTP_404_NOT_FOUND,
          detail="Parent category not found"
        )
      
      if parent.level != 1:
        raise HTTPException(
          status_code=status.HTTP_400_BAD_REQUEST,
          detail="Parent category must be a level 1 category"
        )
      
      category_data.level = 2
    else:
      category_data.level = 1
    
    category_dict = category_data.model_dump()
    category = Category(**category_dict)
    
    db.add(category)
    await db.commit()
    await db.refresh(category)
    
    # 手动构建响应对象，避免访问未加载的关系属性
    return CategoryResponse(
      id=category.id,
      name=category.name,
      description=category.description,
      parent_id=category.parent_id,
      level=category.level,
      is_active=category.is_active,
      created_at=category.created_at,
      updated_at=category.updated_at,
      children=None  # 新创建的分类没有子分类
    )

  @staticmethod
  async def update_category(db: AsyncSession, category_id: int, category_data: CategoryUpdate):
    """更新分类"""
    query = await db.execute(select(Category).where(Category.id == category_id))
    category = query.scalars().first()
    
    if not category:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Category not found"
      )
    
    update_data = category_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
      setattr(category, key, value)
    
    await db.commit()
    await db.refresh(category)
    
    # 如果需要返回子分类，需要查询
    children_query = await db.execute(
      select(Category).where(Category.parent_id == category_id)
    )
    children = children_query.scalars().all()
    
    children_list = None
    if children:
      children_list = [
        CategoryResponse(
          id=child.id,
          name=child.name,
          description=child.description,
          parent_id=child.parent_id,
          level=child.level,
          is_active=child.is_active,
          created_at=child.created_at,
          updated_at=child.updated_at,
          children=None
        )
        for child in children
      ]
    
    # 手动构建响应对象，避免访问未加载的关系属性
    return CategoryResponse(
      id=category.id,
      name=category.name,
      description=category.description,
      parent_id=category.parent_id,
      level=category.level,
      is_active=category.is_active,
      created_at=category.created_at,
      updated_at=category.updated_at,
      children=children_list
    )

  @staticmethod
  async def delete_category(db: AsyncSession, category_id: int):
    """删除分类（如果有关联商品则不允许删除）"""
    query = await db.execute(select(Category).where(Category.id == category_id))
    category = query.scalars().first()
    
    if not category:
      raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Category not found"
      )
    
    # 检查是否有子分类
    children_query = await db.execute(
      select(Category).where(Category.parent_id == category_id)
    )
    children = children_query.scalars().all()
    
    if children:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Cannot delete category with subcategories. Please delete subcategories first."
      )
    
    # 检查是否有关联商品
    from app.models.product import Product
    products_query = await db.execute(
      select(Product).where(Product.category_id == category_id)
    )
    products = products_query.scalars().first()
    
    if products:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Cannot delete category with associated products. Please reassign or delete products first."
      )
    
    await db.delete(category)
    await db.commit()
    
    return {"message": "Category deleted successfully"}

