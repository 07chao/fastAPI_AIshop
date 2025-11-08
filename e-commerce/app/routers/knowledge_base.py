"""
知识库管理路由
用于管理RAG知识库（重建、更新、状态查询）
"""
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status

from app.database.session import get_db
from app.utils.token import get_current_admin
import asyncio

# 可选导入
try:
    from app.services.vector_store_service import VectorStoreService
    from init_knowledge_base import init_knowledge_base
    KNOWLEDGE_BASE_AVAILABLE = True
except ImportError as e:
    KNOWLEDGE_BASE_AVAILABLE = False
    KNOWLEDGE_BASE_ERROR = str(e)
    VectorStoreService = None


router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base"])


@router.get("/status")
async def get_knowledge_base_status():
    """
    获取知识库状态
    """
    if not KNOWLEDGE_BASE_AVAILABLE:
        return JSONResponse(
            content={
                "status": "unavailable",
                "message": f"知识库功能不可用: {KNOWLEDGE_BASE_ERROR}. 请安装依赖: pip install chromadb sentence-transformers"
            },
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        vector_store = VectorStoreService()
        info = vector_store.get_collection_info()
        return {
            "status": "active",
            "collection_name": info["name"],
            "document_count": info["count"],
            "message": "知识库运行正常" if info["status"] == "active" else f"知识库状态: {info['status']}"
        }
    except Exception as e:
        return JSONResponse(
            content={"status": "error", "message": str(e)},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/rebuild")
async def rebuild_knowledge_base(
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_admin)):
    """
    重建知识库（仅管理员）
    删除旧数据并重新构建
    """
    if not KNOWLEDGE_BASE_AVAILABLE:
        return JSONResponse(
            content={"message": f"知识库功能不可用: {KNOWLEDGE_BASE_ERROR}. 请安装依赖: pip install chromadb sentence-transformers"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # 在后台任务中执行（避免阻塞）
        asyncio.create_task(init_knowledge_base(rebuild=True))
        return {
            "message": "知识库重建任务已启动，请稍后查询状态",
            "status": "processing"
        }
    except Exception as e:
        return JSONResponse(
            content={"message": f"重建失败: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/update")
async def update_knowledge_base(
        db: AsyncSession = Depends(get_db),
        current_user=Depends(get_current_admin)):
    """
    增量更新知识库（仅管理员）
    只添加新的商品和评论
    """
    if not KNOWLEDGE_BASE_AVAILABLE:
        return JSONResponse(
            content={"message": f"知识库功能不可用: {KNOWLEDGE_BASE_ERROR}. 请安装依赖: pip install chromadb sentence-transformers"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
    
    try:
        # 在后台任务中执行
        asyncio.create_task(init_knowledge_base(rebuild=False))
        return {
            "message": "知识库更新任务已启动，请稍后查询状态",
            "status": "processing"
        }
    except Exception as e:
        return JSONResponse(
            content={"message": f"更新失败: {str(e)}"},
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

