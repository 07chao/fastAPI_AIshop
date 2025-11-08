from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator
from fastapi import HTTPException, status


class CategoryBase(BaseModel):
  name: str = Field(..., max_length=100, description="分类名称")
  description: Optional[str] = Field(None, max_length=500, description="分类描述")
  
  @field_validator('name', mode='before')
  @classmethod
  def validate_name(cls, value: str) -> str:
    if not value or not value.strip():
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Category name cannot be empty"
      )
    return value.strip()


class CategoryCreate(CategoryBase):
  parent_id: Optional[int] = Field(None, description="父分类ID，如果为NULL则是一级分类")
  level: int = Field(1, ge=1, le=2, description="分类级别：1=一级分类，2=二级分类")


class CategoryUpdate(BaseModel):
  name: Optional[str] = Field(None, max_length=100)
  description: Optional[str] = Field(None, max_length=500)
  is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
  id: int
  parent_id: Optional[int] = None
  level: int
  is_active: bool
  created_at: datetime
  updated_at: Optional[datetime] = None
  children: Optional[List['CategoryResponse']] = None  # 子分类列表
  
  model_config = ConfigDict(from_attributes=True)


# 解决前向引用
CategoryResponse.model_rebuild()

