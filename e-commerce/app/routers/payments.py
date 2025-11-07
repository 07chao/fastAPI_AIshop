from sqlalchemy import select
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.models.payment import Payment
from app.database.session import get_db
from app.utils.token import get_current_user
from app.schemas.payment import PaymentCreate, PaymentStatus
from app.services.payment_service import PaymentServiceMock
from app.responses.payment_response import payment_post_response, stripe_webhook_response


router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/checkout", responses=payment_post_response)
async def create_payment_session(
        request: PaymentCreate,
        db: AsyncSession = Depends(get_db),
        current_user = Depends(get_current_user)):
  """创建Mock支付会话"""
  try:
    checkout_session = await PaymentServiceMock.create_checkout_session(request, db, current_user)
    return checkout_session
  except HTTPException as exc:
    return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

@router.get("/mock-success")
async def mock_payment_success(session_id: str, db: AsyncSession = Depends(get_db)):
  """Mock支付成功 - 模拟支付完成"""
  try:
    payment = await PaymentServiceMock.mock_payment_success(session_id, db)
    return JSONResponse(content={
      "message": "Payment successful (Mock)", 
      "order_id": payment.order_id,
      "amount": payment.amount,
      "status": payment.status
    })
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

@router.get("/mock-cancel")
async def mock_payment_cancel(session_id: str, db: AsyncSession = Depends(get_db)):
  """Mock支付取消 - 模拟支付失败"""
  try:
    payment = await PaymentServiceMock.mock_payment_cancel(session_id, db)
    return JSONResponse(content={
      "message": "Payment canceled (Mock)", 
      "order_id": payment.order_id
    })
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

@router.get("/success")
async def payment_success(session_id: str, db: AsyncSession = Depends(get_db)):
  try:
    result = await db.execute(select(Payment).where(Payment.stripe_session_id == session_id))
    payment = result.scalars().first()
    if not payment:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return JSONResponse(content={"message": "Payment successful", "order_id": payment.order_id})
  except Exception as e:
    return JSONResponse(content=str(e), status_code=status.HTTP_400_BAD_REQUEST)

@router.get("/cancel")
async def payment_cancel(session_id: str, db: AsyncSession = Depends(get_db)):
  try:
    result = await db.execute(select(Payment).where(Payment.stripe_session_id == session_id))
    payment = result.scalars().first()

    payment.status = PaymentStatus.failed

    await db.commit()
    await db.refresh(payment)
    return JSONResponse(content={"message": "Payment failed"})

  except Exception as e:
    return JSONResponse(content=str(e), status_code=status.HTTP_400_BAD_REQUEST)