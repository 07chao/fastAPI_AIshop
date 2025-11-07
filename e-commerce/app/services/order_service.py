from datetime import datetime

from sqlalchemy import func, and_
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Depends

from app.schemas.user import Role
from app.models.product import Product
from app.models.order import OrderStatus
from app.models.cart_item import CartItem
from app.schemas.order import OrderResponse
from app.utils.token import get_current_user
from app.models import Order, User, OrderItem


class OrderService:
  @staticmethod
  async def create_order(db, current_user):
    total_amount = await db.execute(
      select(func.sum(CartItem.quantity * Product.price)).join(Product, CartItem.product_id == Product.id)
      .where(CartItem.user_id == current_user.id))

    total_amount = total_amount.scalar()
    order_data = {"total_amount": total_amount, "user_id": current_user.id}
    order = Order(**order_data)

    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order

  @staticmethod
  async def get_order_by_id(
          order_id: int,
          db: AsyncSession,
          current_user: User = Depends(get_current_user)):

    query = await db.execute(select(Order).filter(Order.id == order_id))
    order = query.scalars().first()

    if not order:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # 允许订单所有者、管理员查看
    if order.user_id == current_user.id or current_user.role == Role.admin:
      return OrderResponse.model_validate(order)
    
    # 如果是商家，检查订单是否包含该商家的商品
    if current_user.role == Role.vendor:
      order_items_query = await db.execute(
        select(OrderItem)
        .join(Product, OrderItem.product_id == Product.id)
        .where(
          and_(
            OrderItem.order_id == order_id,
            Product.vendor_id == current_user.id
          )
        )
      )
      vendor_order_items = order_items_query.scalars().first()
      
      if vendor_order_items:
        return OrderResponse.model_validate(order)
      else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
  
  @staticmethod
  async def cancel_order(
          order_id: int,
          db: AsyncSession,
          current_user: User = Depends(get_current_user)):

    query = await db.execute(select(Order).filter(Order.id == order_id))
    order = query.scalars().first()

    if not order:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    if order.user_id != current_user.id and not current_user.role == Role.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if order.order_status == OrderStatus.canceled:
      raise HTTPException(status_code=status.HTTP_409_CONFLICT,detail="Order already cancelled")

    order.order_status=OrderStatus.canceled

    order_item = await db.execute(select(OrderItem).filter(OrderItem.order_id == order_id))
    order_item = order_item.scalars().first()
    product = await db.execute(select(Product).filter(Product.id == order_item.product_id))
    product = product.scalars().first()
    product.stock = product.stock + order_item.quantity

    await db.commit()
    await db.refresh(order)
    await db.refresh(product)
    return {"message":"Order canceled successfully"}
  
  @staticmethod
  async def confirm_receipt(
          order_id: int,
          db: AsyncSession,
          current_user: User = Depends(get_current_user)):
    """
    用户确认收货接口
    将已发货的订单标记为已完成
    """
    query = await db.execute(select(Order).filter(Order.id == order_id))
    order = query.scalars().first()

    if not order:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # 只有订单所有者可以确认收货
    if order.user_id != current_user.id:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the order owner can confirm receipt")

    # 只能对已发货的订单进行确认收货
    if order.order_status != OrderStatus.shipped:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Cannot confirm receipt for order with status: {order.order_status}. Order must be shipped first."
      )

    # 检查订单是否已经是已完成状态
    if order.order_status == OrderStatus.completed:
      raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="Order has already been confirmed as received"
      )

    # 更新订单状态为已完成
    order.order_status = OrderStatus.completed
    order.updated_at = datetime.now()

    await db.commit()
    await db.refresh(order)

    return {
      "message": "Order confirmed as received successfully",
      "order_id": order.id,
      "order_status": order.order_status.value
    }

  @staticmethod
  async def ship_order(
          order_id: int,
          tracking_number: str,
          db: AsyncSession,
          current_vendor: User = Depends(get_current_user)):
    """
    商家发货接口
    将已支付的订单标记为已发货，并保存快递单号
    """
    query = await db.execute(select(Order).filter(Order.id == order_id))
    order = query.scalars().first()

    if not order:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # 只有商家可以发货（vendor角色）
    if not current_vendor.role == Role.vendor:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only vendors can ship orders")
    
    # 只能对已支付的订单进行发货
    if order.order_status != OrderStatus.paid:
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, 
        detail=f"Cannot ship order with status: {order.order_status}. Order must be paid first."
      )
    
    # 更新订单状态为已发货，并保存快递单号
    order.order_status = OrderStatus.shipped
    order.tracking_number = tracking_number
    order.updated_at = datetime.now()
    
    await db.commit()
    await db.refresh(order)
    
    return {
      "message": "Order shipped successfully",
      "order_id": order.id,
      "order_status": order.order_status.value,
      "tracking_number": order.tracking_number
    }

  @staticmethod
  async def update_order_status(
          order_id: int,
          updated_status: str,
          db: AsyncSession,
          current_user: User = Depends(get_current_user)):

    query = await db.execute(select(Order).filter(Order.id == order_id))
    order = query.scalars().first()

    if not order:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    if not current_user.role == Role.admin:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    
    order.order_status = updated_status
    order.updated_at = datetime.now()
    await db.commit()
    await db.refresh(order)
    return {"message":"Order status updated successfully"}

  @staticmethod
  async def list_orders(
          db: AsyncSession,
          current_user: User = Depends(get_current_user)):

    if current_user.role == Role.admin:
      # 管理员可以查看所有订单
      query = await db.execute(select(Order))
      order = query.scalars().all()
    elif current_user.role == Role.vendor:
      # 商家可以查看包含他们商品的所有订单
      query = await db.execute(
        select(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, OrderItem.product_id == Product.id)
        .where(Product.vendor_id == current_user.id)
        .distinct()
      )
      order = query.scalars().all()
    else:
      # 普通用户只能查看自己的订单
      query = await db.execute(select(Order).filter(Order.user_id == current_user.id)
                               .where(Order.order_status != OrderStatus.canceled))
      order = query.scalars().all()

    if not order:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    return order

  @staticmethod
  async def get_order_by_status(order_status, current_user, db):
    if current_user.role == Role.admin:
      # 管理员可以查看所有状态的订单
      query = await db.execute(
        select(Order).filter(Order.order_status == order_status)
      )
      return query.scalars().all()
    elif current_user.role == Role.vendor:
      # 商家可以查看包含他们商品的指定状态订单
      query = await db.execute(
        select(Order)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .join(Product, OrderItem.product_id == Product.id)
        .where(
          and_(
            Order.order_status == order_status,
            Product.vendor_id == current_user.id
          )
        )
        .distinct()
      )
      return query.scalars().all()
    else:
      # 普通用户只能查看自己指定状态的订单
      query = await db.execute(
        select(Order).filter(
          and_(
            Order.order_status == order_status,
            Order.user_id == current_user.id
          )
        )
      )
      return query.scalars().all()