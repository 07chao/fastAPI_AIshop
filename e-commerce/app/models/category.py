from sqlalchemy import Column, Integer, String, ForeignKey, TIMESTAMP, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class Category(Base):
  __tablename__ = "categories"

  id = Column(Integer, primary_key=True, index=True, autoincrement=True)
  name = Column(String(100), nullable=False)  # 分类名称
  parent_id = Column(Integer, ForeignKey("categories.id"), nullable=True)  # 父分类ID，如果为NULL则是一级分类
  level = Column(Integer, nullable=False, default=1)  # 分类级别：1=一级分类，2=二级分类
  description = Column(String(500), nullable=True)  # 分类描述
  is_active = Column(Boolean, nullable=False, default=True)  # 是否启用
  created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
  updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)

  # 自关联：父分类和子分类的关系
  parent = relationship("Category", remote_side=[id], backref="children")
  
  # 与商品的关系
  products = relationship("Product", back_populates="category_obj")

