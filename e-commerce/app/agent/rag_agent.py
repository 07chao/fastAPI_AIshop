"""
RAG Agent实现
简化版本，专注于商品推荐和购物车操作
"""
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config.settings import settings
from app.services.vector_store_service import VectorStoreService
from app.services.product_service import ProductService
from app.services.cart_item_service import CartService
from app.services.review_service import ReviewService
from app.models.product import Product
from app.models.review import Review
from app.models.user import User
from app.schemas.cart_item import CartItemCreate
import json
import httpx


class RAGAgent:
    """
    RAG Agent
    使用向量检索 + Deepseek API实现智能商品推荐
    """
    
    def __init__(self):
        """初始化Agent"""
        self.vector_store = VectorStoreService()
        self.api_key = settings.DEEPSEEK_API_KEY if hasattr(settings, 'DEEPSEEK_API_KEY') else ""
        self.api_base = settings.DEEPSEEK_API_BASE if hasattr(settings, 'DEEPSEEK_API_BASE') else "https://api.deepseek.com/v1"
    
    async def chat(
        self,
        user_query: str,
        user: User,
        db: AsyncSession
    ) -> Dict:
        """
        与Agent对话
        
        Args:
            user_query: 用户查询
            user: 当前用户
            db: 数据库会话
        
        Returns:
            Dict: 包含回复和推荐商品
        """
        # 1. 使用向量搜索查找相关商品
        search_results = self.vector_store.search(user_query, n_results=10)
        
        # 2. 获取商品详细信息
        product_ids = [int(r["metadata"].get("product_id", r["id"])) for r in search_results if r["metadata"].get("type") == "product"]
        
        products_info = []
        for product_id in product_ids[:5]:  # 只处理前5个
            product_query = await db.execute(
                select(Product).where(Product.id == product_id)
            )
            product = product_query.scalars().first()
            
            if product:
                # 获取评论
                reviews_query = await db.execute(
                    select(Review).where(Review.product_id == product_id)
                )
                reviews = reviews_query.scalars().all()
                
                # 计算性价比
                value_score = self._calculate_value_score(product, reviews)
                
                products_info.append({
                    "id": product.id,
                    "name": product.name,
                    "description": product.description,
                    "price": product.price,
                    "stock": product.stock,
                    "rating": sum(r.rating for r in reviews) / len(reviews) if reviews else 0,
                    "review_count": len(reviews),
                    "value_score": value_score
                })
        
        # 3. 按性价比排序
        products_info.sort(key=lambda x: x["value_score"], reverse=True)
        
        # 4. 使用Deepseek API生成回复
        response_text = await self._generate_response(user_query, products_info)
        
        return {
            "response": response_text,
            "recommended_products": products_info[:3],  # 推荐前3个
            "total_found": len(products_info)
        }
    
    def _calculate_value_score(self, product: Product, reviews: List[Review]) -> float:
        """
        计算性价比分数
        
        Args:
            product: 商品对象
            reviews: 评论列表
        
        Returns:
            float: 性价比分数（0-1）
        """
        if not reviews:
            return 0.0
        
        # 平均评分（归一化到0-1）
        avg_rating = sum(r.rating for r in reviews) / len(reviews) / 5.0
        
        # 价格优势（价格越低分数越高，假设1000元为基准）
        price_score = min(1000 / max(product.price, 1), 1.0)
        
        # 评论数量（归一化，假设50条评论为满分）
        review_count_score = min(len(reviews) / 50.0, 1.0)
        
        # 好评率（4星以上）
        positive_rate = sum(1 for r in reviews if r.rating >= 4) / len(reviews)
        
        # 综合分数
        value_score = (
            avg_rating * 0.4 +
            price_score * 0.3 +
            review_count_score * 0.2 +
            positive_rate * 0.1
        )
        
        return round(value_score, 3)
    
    async def _generate_response(self, user_query: str, products: List[Dict]) -> str:
        """
        使用Deepseek API生成回复
        
        Args:
            user_query: 用户查询
            products: 商品列表
        
        Returns:
            str: AI生成的回复
        """
        if not self.api_key:
            # 如果没有配置API Key，返回简单回复
            if products:
                return f"我为您找到了 {len(products)} 个相关商品。推荐商品：{products[0]['name']}，价格：{products[0]['price']}元，评分：{products[0]['rating']:.1f}星。"
            return "抱歉，没有找到相关商品。"
        
        # 构建提示词
        products_text = "\n".join([
            f"- {p['name']}：价格{p['price']}元，评分{p['rating']:.1f}星，{p['review_count']}条评论，性价比分数{p['value_score']:.2f}"
            for p in products[:3]
        ])
        
        prompt = f"""你是一个专业的电商购物助手。用户查询：{user_query}

我为您找到了以下商品：
{products_text}

请用友好、专业的语气回复用户，推荐性价比最高的商品，并说明推荐理由。如果用户同意，可以帮用户将商品添加到购物车。

回复要求：
1. 用中文回复
2. 语气友好、专业
3. 突出性价比优势
4. 如果商品列表为空，礼貌地说明没有找到相关商品
"""
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek-chat",
                        "messages": [
                            {"role": "system", "content": "你是一个专业的电商购物助手，帮助用户找到性价比最高的商品。"},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.7,
                        "max_tokens": 500
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result["choices"][0]["message"]["content"]
                else:
                    return f"AI服务暂时不可用，但我为您找到了 {len(products)} 个相关商品。"
        except Exception as e:
            print(f"Deepseek API调用失败: {e}")
            # 降级处理
            if products:
                return f"我为您找到了 {len(products)} 个相关商品。推荐：{products[0]['name']}（{products[0]['price']}元，评分{products[0]['rating']:.1f}星）。"
            return "抱歉，没有找到相关商品。"
    
    async def add_to_cart(
        self,
        product_id: int,
        quantity: int,
        user: User,
        db: AsyncSession
    ) -> Dict:
        """
        将推荐的商品添加到购物车
        
        Args:
            product_id: 商品ID
            quantity: 数量
            user: 当前用户
            db: 数据库会话
        
        Returns:
            Dict: 操作结果
        """
        try:
            cart_item_data = CartItemCreate(
                product_id=product_id,
                quantity=quantity
            )
            
            result = await CartService.create_cart_item(cart_item_data, db, user)
            
            return {
                "success": True,
                "message": f"已成功将商品添加到购物车",
                "cart_item": {
                    "id": result.id,
                    "product_id": result.product_id,
                    "quantity": result.quantity,
                    "price": result.price
                }
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"添加到购物车失败: {str(e)}"
            }

