from sqlalchemy import Column, Integer, ForeignKey, Text, TIMESTAMP, CheckConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base


class Review(Base):
  """
  Review模型，代表了用户对商品的评价。
  """
  __tablename__ = "reviews"  # 数据库中的表名

  # --- 字段定义 ---
  id = Column(Integer, primary_key=True, index=True, comment="评价ID，主键")
  user_id = Column(Integer, ForeignKey("users.id"), nullable=False, comment="发表评价的用户ID，外键关联到users表")
  product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="被评价的商品ID，外键关联到products表")
  parent_review_id = Column(Integer, ForeignKey("reviews.id"), nullable=True, comment="父评价ID，用于实现追评功能。如果为NULL，则为一级评价")
  content = Column(Text, nullable=False, comment="评价的具体内容")
  rating = Column(Integer, nullable=False, comment="用户给出的星级评分，例如1-5分")
  likes_count = Column(Integer, nullable=False, default=0, comment="收到的点赞数")
  dislikes_count = Column(Integer, nullable=False, default=0, comment="收到的点踩数")
  created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False, comment="评价创建时间，数据库自动生成")

  # --- 表级别的约束 ---
  __table_args__ = (
    CheckConstraint('likes_count >= 0', name='check_likes_count_non_negative'),
    CheckConstraint('dislikes_count >= 0', name='check_dislikes_count_non_negative'),
    CheckConstraint('rating >= 1 AND rating <= 5', name='check_rating_range'),
  )

  # --- ORM关系定义 ---
  # 与User模型的关系：一个用户可以有多条评价
  user = relationship("User", back_populates="reviews")
  # 与Product模型的关系：一个商品可以有多条评价
  product = relationship("Product", back_populates="reviews")
  # 与Review模型的自关联关系：用于实现评价的层级结构（主评论与追评）
  # remote_side=[id] 指定了关联的远程侧是当前表的id列
  # backref="follow_up_reviews" 使得可以从一个主评论对象通过 .follow_up_reviews 访问其所有的追评
  parent_review = relationship("Review", remote_side=[id], backref="follow_up_reviews")