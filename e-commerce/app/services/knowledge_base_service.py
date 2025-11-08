"""
知识库服务
用于提取和准备商品、评论数据，构建RAG知识库
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict
from app.models.product import Product
from app.models.review import Review
from app.models.category import Category


class KnowledgeBaseService:
    """
    知识库服务
    负责从数据库提取商品和评论数据，构建知识文档
    """
    
    @staticmethod
    async def extract_all_products(db: AsyncSession) -> List[Dict]:
        """
        提取所有商品信息
        
        Returns:
            List[Dict]: 商品信息列表，每个商品包含完整信息
        """
        # 检查Product模型是否有category_id字段
        has_category_id = hasattr(Product, 'category_id')
        
        if has_category_id:
            # 使用category_id关联Category表
            query = await db.execute(
                select(Product, Category)
                .join(Category, Product.category_id == Category.id)
                .where(Product.is_active == True)
            )
            results = query.all()
            
            products_data = []
            for product, category in results:
                # 构建商品知识文档
                product_doc = {
                    "id": product.id,
                    "type": "product",
                    "name": product.name,
                    "description": product.description or "",
                    "price": product.price,
                    "stock": product.stock,
                    "category": category.name,
                    "category_level": category.level,
                    "view_count": product.view_count,
                    "created_at": str(product.created_at),
                    # 构建完整的文本内容用于Embedding
                    "text": f"""
商品名称：{product.name}
商品描述：{product.description or '无描述'}
价格：{product.price}元
分类：{category.name}
库存：{product.stock}
浏览量：{product.view_count}
""".strip()
                }
                products_data.append(product_doc)
        else:
            # 使用旧的category枚举字段
            query = await db.execute(
                select(Product).where(Product.is_active == True)
            )
            results = query.scalars().all()
            
            products_data = []
            for product in results:
                # 构建商品知识文档
                product_doc = {
                    "id": product.id,
                    "type": "product",
                    "name": product.name,
                    "description": product.description or "",
                    "price": product.price,
                    "stock": product.stock,
                    "category": product.category.value if hasattr(product.category, 'value') else str(product.category),
                    "view_count": product.view_count,
                    "created_at": str(product.created_at),
                    # 构建完整的文本内容用于Embedding
                    "text": f"""
商品名称：{product.name}
商品描述：{product.description or '无描述'}
价格：{product.price}元
分类：{product.category.value if hasattr(product.category, 'value') else str(product.category)}
库存：{product.stock}
浏览量：{product.view_count}
""".strip()
                }
                products_data.append(product_doc)
        
        return products_data
    
    @staticmethod
    async def extract_all_reviews(db: AsyncSession) -> List[Dict]:
        """
        提取所有评论信息
        
        Returns:
            List[Dict]: 评论信息列表
        """
        # 只提取主评论（parent_review_id为NULL）
        query = await db.execute(
            select(Review, Product)
            .join(Product, Review.product_id == Product.id)
            .where(Review.parent_review_id.is_(None))
        )
        results = query.all()
        
        reviews_data = []
        for review, product in results:
            # 构建评论知识文档
            review_doc = {
                "id": review.id,
                "type": "review",
                "product_id": review.product_id,
                "product_name": product.name,
                "content": review.content,
                "rating": review.rating,
                "likes_count": review.likes_count,
                "dislikes_count": review.dislikes_count,
                "created_at": str(review.created_at),
                # 构建完整的文本内容用于Embedding
                "text": f"""
商品：{product.name}
评分：{review.rating}星
评论内容：{review.content}
点赞数：{review.likes_count}
点踩数：{review.dislikes_count}
""".strip()
            }
            reviews_data.append(review_doc)
        
        return reviews_data
    
    @staticmethod
    async def build_knowledge_documents(db: AsyncSession) -> List[Dict]:
        """
        构建完整的知识文档列表
        
        Returns:
            List[Dict]: 包含商品和评论的知识文档列表
        """
        products = await KnowledgeBaseService.extract_all_products(db)
        reviews = await KnowledgeBaseService.extract_all_reviews(db)
        
        # 组合商品和评论
        documents = products + reviews
        
        return documents
    
    @staticmethod
    def format_document_for_embedding(doc: Dict) -> str:
        """
        格式化文档为适合Embedding的文本
        
        Args:
            doc: 知识文档字典
        
        Returns:
            str: 格式化后的文本
        """
        return doc.get("text", "")

