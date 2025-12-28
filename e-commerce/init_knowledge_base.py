"""
初始化知识库脚本
从数据库提取商品和评论，生成向量并存储到向量数据库
"""
import asyncio
from app.database.session import get_db
from app.services.knowledge_base_service import KnowledgeBaseService
from app.services.vector_store_service import VectorStoreService


async def init_knowledge_base(rebuild: bool = True):
    """
    初始化知识库
    
    Args:
        rebuild: 是否重建（删除旧数据）
    """
    print("=" * 50)
    print("开始构建知识库...")
    print("=" * 50)
    
    # 初始化向量数据库
    vector_store = VectorStoreService()
    
    if rebuild:
        print("正在删除旧的知识库...")
        vector_store.delete_collection()
        # 重新初始化
        vector_store = VectorStoreService()
    
    # 获取数据库连接
    async for db in get_db():
        try:
            # 提取所有数据
            print("\n1. 正在提取商品数据...")
            products = await KnowledgeBaseService.extract_all_products(db)
            print(f"   提取到 {len(products)} 个商品")
            
            print("\n2. 正在提取评论数据...")
            reviews = await KnowledgeBaseService.extract_all_reviews(db)
            print(f"   提取到 {len(reviews)} 条评论")
            
            # 构建知识文档
            print("\n3. 正在构建知识文档...")
            documents = await KnowledgeBaseService.build_knowledge_documents(db)
            print(f"   共 {len(documents)} 个知识文档")
            
            # 添加到向量数据库
            print("\n4. 正在生成向量并存储到向量数据库...")
            vector_store.add_documents(documents, batch_size=50)
            
            # 显示统计信息
            print("\n5. 知识库构建完成！")
            info = vector_store.get_collection_info()
            print(f"   集合名称: {info['name']}")
            print(f"   文档数量: {info['count']}")
            print(f"   状态: {info['status']}")
            
        except Exception as e:
            print(f"\n错误: {e}")
            import traceback
            traceback.print_exc()
        finally:
            break
    
    print("\n" + "=" * 50)
    print("知识库构建完成！")
    print("=" * 50)


if __name__ == "__main__":
    import sys
    rebuild = "--rebuild" in sys.argv
    asyncio.run(init_knowledge_base(rebuild=rebuild))

