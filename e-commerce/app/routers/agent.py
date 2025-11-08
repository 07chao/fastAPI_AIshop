"""
AI Agent路由
提供智能商品推荐和购物车操作接口
"""
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List

from app.database.session import get_db
from app.utils.token import get_current_user
from app.agent.rag_agent import RAGAgent
from app.models.user import User


router = APIRouter(prefix="/agent", tags=["AI Agent"])


class ChatRequest(BaseModel):
    """对话请求"""
    query: str = Field(..., description="用户查询（自然语言）")
    context: Optional[dict] = Field(None, description="上下文信息（可选）")


class AddToCartRequest(BaseModel):
    """添加到购物车请求"""
    product_id: int = Field(..., description="商品ID")
    quantity: int = Field(1, ge=1, description="数量")


@router.post("/chat")
async def chat_with_agent(
        request: ChatRequest,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user)):
    """
    与AI Agent对话
    支持自然语言查询，Agent会智能推荐商品
    """
    try:
        agent = RAGAgent()
        result = await agent.chat(
            user_query=request.query,
            user=current_user,
            db=db
        )
        return result
    except HTTPException as exc:
        return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
    except Exception as e:
        return JSONResponse(
            content={"message": f"Agent处理失败: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/recommend")
async def recommend_products(
        query: str,
        max_results: int = 5,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user)):
    """
    获取商品推荐
    """
    try:
        agent = RAGAgent()
        result = await agent.chat(
            user_query=query,
            user=current_user,
            db=db
        )
        return {
            "recommended_products": result.get("recommended_products", []),
            "total_found": result.get("total_found", 0)
        }
    except HTTPException as exc:
        return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
    except Exception as e:
        return JSONResponse(
            content={"message": f"推荐失败: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/add-to-cart")
async def agent_add_to_cart(
        request: AddToCartRequest,
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_user)):
    """
    Agent自动添加到购物车
    """
    try:
        agent = RAGAgent()
        result = await agent.add_to_cart(
            product_id=request.product_id,
            quantity=request.quantity,
            user=current_user,
            db=db
        )
        return result
    except HTTPException as exc:
        return JSONResponse(content={"message": str(exc)}, status_code=exc.status_code)
    except Exception as e:
        return JSONResponse(
            content={"message": f"添加到购物车失败: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

