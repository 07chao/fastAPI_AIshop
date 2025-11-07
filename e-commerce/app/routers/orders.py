from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status

from app.database.session import get_db
from app.schemas.order import OrderResponse, ShipOrderRequest
from app.utils.token import get_current_user, get_current_admin, get_current_vendor
from app.services.order_service import OrderService
from app.responses.order_responses import order_responses


router = APIRouter(prefix="/orders", tags=["Orders"])

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
        order_id: int,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user)):
  try:
    order_by_id = await OrderService.get_order_by_id(order_id, db, current_user)
    return order_by_id
  except HTTPException as exc:
      return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
  
@router.patch("/cancel/{order_id}", responses=order_responses)
async def cancel_order(
        order_id: int,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user)):
  try:
    canceled_order = await OrderService.cancel_order(order_id, db, current_user)
    return canceled_order
  except HTTPException as exc:
      return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

@router.patch("/confirm-receipt/{order_id}", responses=order_responses)
async def confirm_receipt(
        order_id: int,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user)):
  """
  用户确认收货接口
  只有订单所有者可以将已发货的订单标记为已完成
  """
  try:
    confirmed_order = await OrderService.confirm_receipt(order_id, db, current_user)
    return confirmed_order
  except HTTPException as exc:
      return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)
  
@router.get("/")
async def list_orders(
        db: AsyncSession = Depends(get_db),
        current_user = Depends(get_current_user)):
  try:
    orders = await OrderService.list_orders(db, current_user)
    return orders
  except HTTPException as exc:
      return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

@router.get("/status/{order_status}")
async def list_orders_by_status(
        order_status: str,
        current_user=Depends(get_current_user),
        db: AsyncSession = Depends(get_db)):
  try:
    order_by_status = await OrderService.get_order_by_status(order_status, current_user, db)
    return order_by_status
  except HTTPException as exc:
      return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)

@router.patch("/ship/{order_id}", responses=order_responses)
async def ship_order(
        order_id: int,
        ship_request: ShipOrderRequest,
        db: AsyncSession = Depends(get_db),
        current_vendor=Depends(get_current_vendor)):
  """
  商家发货接口
  只有商家（vendor）可以将已支付的订单标记为已发货
  需要提供快递单号
  """
  try:
    shipped_order = await OrderService.ship_order(
      order_id, 
      ship_request.tracking_number, 
      db, 
      current_vendor
    )
    return shipped_order
  except HTTPException as exc:
      return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
  except Exception as e:
    return JSONResponse(content={"message": str(e)}, status_code=status.HTTP_400_BAD_REQUEST)