from datetime import datetime
from sqlalchemy import select, and_, or_
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import Review
from app.models.product import Product
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.schemas.review import LikeDislike
from app.database.redis_session import redis_connection
from app.schemas.review import ReviewCreate, ReviewResponse


class ReviewService:
  @staticmethod
  async def get_my_reviews(db: AsyncSession, user):
    reviews= await db.execute(select(Review).where(Review.user_id == user.id))
    result= reviews.scalars().all()

    return result

  @staticmethod
  async def get_review_by_id(product_id: int, db: AsyncSession):
    """
    获取商品的所有主评论，每个主评论包含其追评列表
    """
    # 查询该商品的所有主评论（parent_review_id 为 NULL）
    main_reviews_query = await db.execute(
      select(Review).where(
        and_(
          Review.product_id == product_id,
          Review.parent_review_id.is_(None)
        )
      ).order_by(Review.created_at.desc())
    )
    main_reviews = main_reviews_query.scalars().all()

    if not main_reviews:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No reviews found for this product")

    # 为每个主评论查询其追评列表
    result = []
    for main_review in main_reviews:
      # 查询该主评论的所有追评
      follow_up_query = await db.execute(
        select(Review).where(
          Review.parent_review_id == main_review.id
        ).order_by(Review.created_at.asc())
      )
      follow_up_reviews = follow_up_query.scalars().all()

      # 构建追评列表
      follow_up_list = [
        ReviewResponse(
          id=fu.id,
          product_id=fu.product_id,
          parent_review_id=fu.parent_review_id,
          content=fu.content,
          rating=fu.rating,
          created_at=fu.created_at,
          follow_up_reviews=None  # 追评不能再有追评
        )
        for fu in follow_up_reviews
      ] if follow_up_reviews else None

      # 构建主评论响应对象
      main_review_response = ReviewResponse(
        id=main_review.id,
        product_id=main_review.product_id,
        parent_review_id=main_review.parent_review_id,
        content=main_review.content,
        rating=main_review.rating,
        created_at=main_review.created_at,
        follow_up_reviews=follow_up_list
      )
      result.append(main_review_response)

    return result

  @staticmethod
  async def create_review(review: ReviewCreate, db: AsyncSession,current_user):
    if not current_user:
      return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is not authorized")

    # 1. 检查商品是否存在
    existing_product_query = await db.execute(select(Product).where(Product.id == review.product_id))
    existing_product = existing_product_query.scalar_one_or_none()

    if not existing_product:
      raise HTTPException(detail="Product not found with that id",status_code=status.HTTP_404_NOT_FOUND)

    # 2. 检查用户是否购买过该商品且订单已完成（completed 或 shipped）
    purchased_query = await db.execute(
      select(Order)
      .join(OrderItem, OrderItem.order_id == Order.id)
      .where(
        and_(
          Order.user_id == current_user.id,
          OrderItem.product_id == review.product_id,
          or_(
            Order.order_status == OrderStatus.completed,  # 已完成
            Order.order_status == OrderStatus.shipped     # 已发货
          )
        )
      )
    )
    purchased_order = purchased_query.scalar_one_or_none()

    if not purchased_order:
      raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="You can only review products you have purchased and received (order status: shipped or completed)."
      )

    # 3. 检查用户是否已经评论过该商品（查找主评论）
    existing_review_query = await db.execute(
      select(Review).where(
        and_(
          Review.user_id == current_user.id,
          Review.product_id == review.product_id,
          Review.parent_review_id.is_(None)  # 查找主评论
        )
      )
    )
    existing_review = existing_review_query.scalar_one_or_none()

    # 4. 创建评论或追评
    review_dict = review.model_dump()
    review_dict["user_id"] = current_user.id
    
    if existing_review:
      # 如果已存在主评论，创建追评
      review_dict["parent_review_id"] = existing_review.id
      review_dict["rating"] = None  # 追评不需要评分，使用主评论的评分
    else:
      # 如果不存在主评论，创建主评论
      review_dict["parent_review_id"] = None

    # 创建 Review 对象（追评时 rating 可能为 None，需要处理）
    review_data = {
      "user_id": review_dict["user_id"],
      "product_id": review_dict["product_id"],
      "content": review_dict["content"],
      "parent_review_id": review_dict.get("parent_review_id")
    }
    
    # 只有主评论需要 rating
    if not existing_review:
      review_data["rating"] = review_dict["rating"]
    else:
      # 追评使用主评论的评分
      review_data["rating"] = existing_review.rating

    review_db = Review(**review_data)
    db.add(review_db)
    await db.commit()
    await db.refresh(review_db)

    # 手动构建 ReviewResponse，避免访问关系属性导致的异步加载问题
    return ReviewResponse(
      id=review_db.id,
      product_id=review_db.product_id,
      parent_review_id=review_db.parent_review_id,
      content=review_db.content,
      rating=review_db.rating,
      created_at=review_db.created_at,
      follow_up_reviews=None  # 新创建的评论没有追评
    )

  @staticmethod
  async def update_review(
          review_id: int,
          updated_review: ReviewCreate,
          db: AsyncSession, user):

    review = await db.execute(select(Review).where(Review.id==review_id))
    review_dict = review.scalars().first()

    if not review_dict:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if review_dict.user_id != user.id:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission to perform this action")

    review_dict.content= updated_review.content
    review_dict.rating= updated_review.rating

    db.add(review_dict)
    await db.commit()
    await db.refresh(review_dict)

    return review_dict

  @staticmethod
  async def delete_review(review_id: int, db: AsyncSession, user):
    review = await db.execute(select(Review).where(Review.id==review_id))
    review_dict= review.scalars().first()

    if not review_dict:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")

    if review_dict.user_id != user.id:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You have no permission to perform this action")

    await db.delete(review_dict)
    await db.commit()
  
  @staticmethod
  async def like_dislike(reaction: LikeDislike, db: AsyncSession, current_user):
    review_query = await db.execute(select(Review).where(Review.id == reaction.review_id))
    review = review_query.scalars().first()

    if not review:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Review not found")

    key = f"review:{review.id}:user:{current_user.id}:reaction"
    previous_state = await redis_connection.get(key)

    like = "like"
    dislike = "dislike"

    if previous_state == like and reaction.like_dislike == 1:
        review.likes_count -= 1
        await redis_connection.delete(key)

    elif previous_state == dislike and reaction.like_dislike == 0:
        review.dislikes_count -= 1
        await redis_connection.delete(key)

    elif reaction.like_dislike == 1:
        review.likes_count += 1
        review.dislikes_count -= 1 if previous_state == dislike else 0
        await redis_connection.set(key, like)

    else:
        review.dislikes_count += 1
        review.likes_count -= 1 if previous_state == like else 0
        await redis_connection.set(key, dislike)
    
    db.add(review)
    await db.commit()
    await db.refresh(review)

    return review