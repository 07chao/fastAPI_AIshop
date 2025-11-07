from datetime import datetime
from enum import Enum
from typing import Optional

from fastapi import HTTPException, status
from pydantic import BaseModel, ConfigDict, Field, field_validator


class OrderStatus(str, Enum):
  pending = "pending"
  paid = "paid"
  shipped = "shipped"
  canceled = "canceled"
  completed = "completed"

class OrderBase(BaseModel):
  total_amount: float = Field(..., ge=0,
                    json_schema_extra={"description": "Total amount must be greater than 0"})

  order_status: OrderStatus = Field(json_schema_extra={"description": "Order status"})
  model_config = ConfigDict(from_attributes=True, use_enum_values=True)

  @field_validator("total_amount", mode="before")
  @classmethod
  def validate_total_amount(cls, total_amount: float) -> float:
    if total_amount <= 0:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Total Amount must be greater than 0."
      )
    return total_amount

class OrderCreate(OrderBase):
  pass

class OrderUpdate(OrderBase):
  pass

class OrderResponse(OrderBase):
  created_at: datetime
  updated_at: Optional[datetime] = None
  id: int
  tracking_number: Optional[str] = None  # 快递单号

class ShipOrderRequest(BaseModel):
  """商家发货时需要提供的快递单号"""
  tracking_number: str = Field(..., min_length=5, max_length=100,
                                json_schema_extra={"description": "快递单号，长度5-100字符"})
  
  model_config = ConfigDict(from_attributes=True)
  
  @field_validator("tracking_number", mode="before")
  @classmethod
  def validate_tracking_number(cls, tracking_number: str) -> str:
    if not tracking_number or not tracking_number.strip():
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tracking number cannot be empty."
      )
    
    tracking_number = tracking_number.strip()
    
    if len(tracking_number) < 5:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tracking number must be at least 5 characters long."
      )
    
    if len(tracking_number) > 100:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Tracking number must be at most 100 characters long."
      )
    
    return tracking_number