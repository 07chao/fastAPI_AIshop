"""
Agent工具定义
定义Agent可用的工具函数
"""
from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.vector_store_service import VectorStoreService
from app.services.product_service import ProductService
from app.services.cart_item_service import CartService
from app.schemas.cart_item import CartItemCreate


# 全局向量存储服务实例（将在初始化时创建）
vector_store: Optional[VectorStoreService] = None


def init_vector_store():
    """初始化向量存储服务"""
    global vector_store
    if vector_store is None:
        vector_store = VectorStoreService()
    return vector_store


def search_products_by_semantic(query: str, n_results: int = 10) -> str:
    """
    使用语义搜索查找商品
    
    Args:
        query: 搜索查询（自然语言）
        n_results: 返回结果数量
    
    Returns:
        str: JSON格式的搜索结果
    """
    try:
        store = init_vector_store()
        results = store.search(query, n_results=n_results)
        
        # 格式化结果
        formatted = []
        for r in results:
            formatted.append({
                "id": r["id"],
                "type": r["metadata"].get("type"),
                "product_id": r["metadata"].get("product_id"),
                "product_name": r["metadata"].get("product_name"),
                "price": r["metadata"].get("price"),
                "rating": r["metadata"].get("rating"),
                "category": r["metadata"].get("category"),
                "text": r["text"][:200] + "..." if len(r["text"]) > 200 else r["text"],
                "relevance_score": 1 - r["distance"] if r["distance"] else 0
            })
        
        import json
        return json.dumps(formatted, ensure_ascii=False, indent=2)
    except ValueError as e:
        # 向量数据库为空或损坏
        import json
        return json.dumps({
            "error": str(e),
            "message": "向量数据库未初始化或已损坏，请运行初始化脚本"
        }, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"搜索失败: {str(e)}"


def get_product_details(product_id: int) -> str:
    """
    获取商品详细信息
    
    Args:
        product_id: 商品ID
    
    Returns:
        str: JSON格式的商品详情
    """
    # 这个工具需要在Agent中异步调用，这里只是定义接口
    return f"需要异步调用ProductService.get_product_by_id({product_id})"


def add_product_to_cart(product_id: int, quantity: int = 1) -> str:
    """
    将商品添加到购物车
    
    Args:
        product_id: 商品ID
        quantity: 数量
    
    Returns:
        str: 操作结果
    """
    # 这个工具需要在Agent中异步调用，这里只是定义接口
    return f"需要异步调用CartService.create_cart_item(product_id={product_id}, quantity={quantity})"


def compare_products(product_ids: List[int]) -> str:
    """
    比较多个商品
    
    Args:
        product_ids: 商品ID列表
    
    Returns:
        str: JSON格式的比较结果
    """
    return f"需要异步调用ProductService比较商品 {product_ids}"


def filter_products_by_conditions(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[int] = None
) -> str:
    """
    根据条件过滤商品
    
    Args:
        category: 分类
        min_price: 最低价格
        max_price: 最高价格
        min_rating: 最低评分
    
    Returns:
        str: JSON格式的过滤结果
    """
    return f"需要根据条件过滤: category={category}, price={min_price}-{max_price}, rating>={min_rating}"


def get_agent_tools() -> List:
    """
    获取所有Agent工具列表
    
    Returns:
        List: 工具列表
    """
    return [
        search_products_by_semantic,
        get_product_details,
        add_product_to_cart,
        compare_products,
        filter_products_by_conditions
    ]

