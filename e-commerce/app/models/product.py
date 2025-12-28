from sqlalchemy import Column, Integer, String, Float, Text, TIMESTAMP, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class Product(Base):
  __tablename__ = "products"

  id = Column(Integer, primary_key=True, index=True, autoincrement=True)
  name = Column(String(100), nullable=False)
  description = Column(Text, nullable=True)
  price = Column(Float, nullable=False)
  stock = Column(Integer, nullable=False)
  category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
  vendor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
  created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
  updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
  is_active = Column(Boolean, nullable=False)
  image_url = Column(String, nullable=True)
  view_count = Column(Integer, default=0)
  # 新增字段：平均评分和评价总数，用于优化性能
  average_rating = Column(Float, nullable=False, default=0.0, comment="商品平均评分")
  review_count = Column(Integer, nullable=False, default=0, comment="商品评价总数")

  # 与Category的关系
  category_obj = relationship("Category", back_populates="products")
  
  order_items = relationship("OrderItem", back_populates="product", cascade="all, delete-orphan")
  cart_items = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
  reviews = relationship("Review", back_populates="product", cascade="all, delete-orphan")
  wishlist = relationship("Wishlist", back_populates="product", cascade="all, delete-orphan")