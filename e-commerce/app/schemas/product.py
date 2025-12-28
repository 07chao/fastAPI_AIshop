from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator

class ProductBase(BaseModel):
  name: str = Field(..., max_length=100)
  description: Optional[str] = Field(None, max_length=500)
  price: float = Field(..., gt=0)
  stock: int = Field(..., ge=0)
  category_id: int = Field(..., description="分类ID")  # 使用分类ID而不是枚举
  image_url: Optional[str] = Field(None)
  
  model_config = ConfigDict(from_attributes=True)
    
  @field_validator('name', mode='before')
  @classmethod
  def validate_non_empty(cls, value: str, info) -> str:
    if not isinstance(value, str):
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"'{info.field_name}' must be string")
    if not value.strip():
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"'{info.field_name}' can't be empty.")
    return value
  
  @field_validator('category_id', mode='before')
  @classmethod
  def validate_category_id(cls, value: Optional[int]) -> Optional[int]:
    if value is not None and value < 1:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="category_id must be a positive integer")
    return value
  
  @field_validator('description', mode='before')
  @classmethod
  def validate_description(cls, value: Optional[str]) -> Optional[str]:
    if value and len(value) > 500:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Description too long.")
    if not value.strip():
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Description can't be empty.")
    return value
  
  @field_validator('price', mode='before')
  @classmethod
  def validate_price(cls, value: float) -> float:
    if value < 0:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be positive")
    return value
  
  @field_validator('stock', mode='before')
  @classmethod
  def validate_stock(cls, value: int) -> int:
    if value < 0:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock field must be positive")
    return value
  
class ProductCreate(ProductBase):
  pass

class ProductResponse(ProductBase):
  id: int
  created_at: datetime
  updated_at: Optional[datetime] = None
  # 新增字段，用于在API响应中返回商品的评分信息
  average_rating: float = Field(0.0, description="商品平均评分")
  review_count: int = Field(0, description="商品评价总数")

  model_config = ConfigDict(from_attributes=True)

class ProductUpdate(BaseModel):
  name: Optional[str] = Field(None, max_length=100)
  description: Optional[str] = Field(None, max_length=500)
  price: Optional[float] = Field(None, gt=0)
  stock: Optional[int] = Field(None, ge=0)
  category_id: Optional[int] = Field(None, description="分类ID")
  image_url: Optional[str] = Field(None, json_schema_extra={"description" : "URL of the product's image"})

  @field_validator('name', 'description', 'image_url', mode="before")
  @classmethod
  def validate_optional_fields(cls, value: Optional[str], info) -> Optional[str]:
        if value is not None and not str(value).strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"The field '{info.field_name}' can't be empty."
            )
        return value
  
  @field_validator('category_id', mode='before')
  @classmethod
  def validate_category_id(cls, value: Optional[int]) -> Optional[int]:
    if value is not None and value < 1:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="category_id must be a positive integer")
    return value
  
  @field_validator('price',mode='before')
  @classmethod
  def validate_price(cls, value: Optional[float]) -> Optional[float]:
    if value < 0:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Price must be positive")
    return value
  
  @field_validator('stock',mode='before')
  @classmethod
  def validate_stock(cls, value: Optional[int]) -> Optional[int]:
    if value < 0:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Stock must be positive")
    return value
  
class ProductFilter(BaseModel):
  page: int = 1
  size: int = 10
  category_id: Optional[int] = None  # 使用分类ID
  min_price: Optional[float] = None
  max_price: Optional[float] = None
  availability: Optional[bool] = None

  @field_validator('min_price', 'max_price', mode="before")
  @classmethod
  def validate_optional_fields(cls, value: Optional[float], info) -> Optional[float]:
    if value is not None and float(value) < 0:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"The field '{info.field_name}' can't be negative."
        )
    return value