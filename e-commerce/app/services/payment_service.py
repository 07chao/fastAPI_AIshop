import uuid
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order
from app.models.payment import Payment
from app.models.user import User
from app.schemas.order import OrderStatus
from app.schemas.payment import PaymentCreate, PaymentStatus
from app.services.email_service import EmailService


class PaymentServiceMock:
  @staticmethod
  async def create_checkout_session(
          request: PaymentCreate,
          db: AsyncSession, current_user):
    """Mock支付 - 不需要真实支付，直接模拟支付成功"""
    
    query = select(Order).where(Order.id == request.order_id).filter(Order.order_status == OrderStatus.pending)
    result = await db.execute(query)
    order = result.scalars().first()

    if not order:
      raise HTTPException(status_code=404, detail="Order not found")

    if order.user_id != current_user.id:
      raise HTTPException(status_code=403, detail="Unauthorized to make payment for this order")

    # 生成Mock的session_id
    mock_session_id = f"mock_session_{uuid.uuid4().hex[:24]}"
    
    # 创建支付记录
    new_payment = Payment(
      amount=order.total_amount,
      currency=request.currency,
      user_id=current_user.id,
      order_id=order.id,
      stripe_session_id=mock_session_id,
      status=PaymentStatus.pending)

    db.add(new_payment)
    await db.commit()
    await db.refresh(new_payment)
    
    # 返回Mock的支付链接
    mock_checkout_url = f"http://localhost:3000/mock-payment?session_id={mock_session_id}&order_id={order.id}&amount={order.total_amount}"
    
    return {
      "session_id": mock_session_id, 
      "checkout_url": mock_checkout_url,
      "message": "Mock payment - 访问 /payments/mock-success?session_id={session_id} 来模拟支付成功"
    }

  @staticmethod
  async def mock_payment_success(session_id: str, db: AsyncSession):
    """模拟支付成功"""
    
    result = await db.execute(select(Payment).where(Payment.stripe_session_id == session_id))
    payment = result.scalars().first()

    if not payment:
      raise HTTPException(status_code=404, detail="Payment not found")

    # 检查支付是否已经完成
    if payment.status == PaymentStatus.completed:
      raise HTTPException(
        status_code=400, 
        detail="Payment already completed. Cannot process again.")
    
    # 检查支付是否已经失败
    if payment.status == PaymentStatus.failed:
      raise HTTPException(
        status_code=400, 
        detail="Payment already failed. Cannot mark as successful.")

    # 获取订单并检查状态
    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalars().first()
    
    if not order:
      raise HTTPException(status_code=404, detail="Order not found")
    
    # 检查订单是否已经支付
    if order.order_status == OrderStatus.paid:
      raise HTTPException(
        status_code=400, 
        detail="Order already paid. Cannot process payment again.")
    
    # 检查订单是否已经取消
    if order.order_status == OrderStatus.canceled:
      raise HTTPException(
        status_code=400, 
        detail="Order is canceled. Cannot process payment.")

    # 更新支付状态
    payment.status = PaymentStatus.completed

    # 更新订单状态
    order.order_status = OrderStatus.paid

    # 获取用户信息
    user_query = await db.execute(select(User).where(User.id == payment.user_id))
    user = user_query.scalars().first()

    db.add(payment)
    db.add(order)
    await db.commit()
    await db.refresh(payment)
    await db.refresh(order)

    # 发送支付成功邮件（可选）
    if user:
      try:
        await EmailService.payment_confirmation_message(user.email)
      except:
        pass  # 邮件发送失败不影响支付流程

    return payment
  
  @staticmethod
  async def mock_payment_cancel(session_id: str, db: AsyncSession):
    """模拟支付取消"""
    
    result = await db.execute(select(Payment).where(Payment.stripe_session_id == session_id))
    payment = result.scalars().first()

    if not payment:
      raise HTTPException(status_code=404, detail="Payment not found")

    # 检查支付是否已经完成
    if payment.status == PaymentStatus.completed:
      raise HTTPException(
        status_code=400, 
        detail="Payment already completed. Cannot cancel a successful payment.")
    
    # 检查支付是否已经失败
    if payment.status == PaymentStatus.failed:
      raise HTTPException(
        status_code=400, 
        detail="Payment already failed. Cannot cancel again.")
    
    # 获取订单并检查状态
    order_result = await db.execute(select(Order).where(Order.id == payment.order_id))
    order = order_result.scalars().first()
    
    if order:
      # 检查订单是否已经支付
      if order.order_status == OrderStatus.paid:
        raise HTTPException(
          status_code=400, 
          detail="Order already paid. Cannot cancel the payment.")
      
      # 检查订单是否已经取消
      if order.order_status == OrderStatus.canceled:
        raise HTTPException(
          status_code=400, 
          detail="Order already canceled.")

    # 更新支付状态
    payment.status = PaymentStatus.failed

    db.add(payment)
    await db.commit()
    await db.refresh(payment)

    return payment