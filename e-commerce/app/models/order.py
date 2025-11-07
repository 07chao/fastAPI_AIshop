import enum
from sqlalchemy import Column, Integer, Float, ForeignKey, TIMESTAMP, Enum, String
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.models.base import Base


class OrderStatus(str, enum.Enum):
  pending = "pending"
  paid = "paid"
  shipped = "shipped"
  completed = "completed"  # 已完成/已签收
  canceled = "canceled"


class Order(Base):
  __tablename__ = "orders"

  id = Column(Integer, primary_key=True, index=True, autoincrement=True)
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  total_amount = Column(Float, nullable=False)
  order_status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.pending)
  tracking_number = Column(String(100), nullable=True)  # 快递单号
  created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
  updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

  user = relationship("User", back_populates="orders")
  order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
  payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")