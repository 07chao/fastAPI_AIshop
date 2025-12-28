"""
检查向量数据库状态脚本
用于诊断和修复向量数据库问题
"""
import asyncio
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.vector_store_service import VectorStoreService


def check_vector_db():
    """检查向量数据库状态"""
    print("=" * 60)
    print("向量数据库诊断工具")
    print("=" * 60)
    
    try:
        vector_store = VectorStoreService()
        
        # 检查集合信息
        print("\n1. 检查集合状态...")
        info = vector_store.get_collection_info()
        print(f"   集合名称: {info['name']}")
        print(f"   文档数量: {info['count']}")
        print(f"   状态: {info['status']}")
        
        # 检查是否为空
        print("\n2. 检查集合是否为空...")
        is_empty = vector_store.is_collection_empty()
        if is_empty:
            print("   ⚠️  集合为空！")
            print("\n   解决方案:")
            print("   运行以下命令初始化知识库:")
            print("   python -m e-commerce.init_knowledge_base")
        else:
            print("   ✓ 集合包含数据")
        
        # 尝试执行一个简单的搜索测试
        print("\n3. 测试搜索功能...")
        try:
            results = vector_store.search("测试", n_results=1)
            print(f"   ✓ 搜索功能正常，找到 {len(results)} 个结果")
        except ValueError as e:
            print(f"   ⚠️  搜索失败: {e}")
            print("\n   解决方案:")
            if "为空" in str(e) or "未初始化" in str(e):
                print("   运行以下命令初始化知识库:")
                print("   python -m e-commerce.init_knowledge_base")
            elif "损坏" in str(e) or "不完整" in str(e):
                print("   运行以下命令重建知识库:")
                print("   python -m e-commerce.init_knowledge_base --rebuild")
        except Exception as e:
            error_msg = str(e)
            if "hnsw" in error_msg.lower() or "segment reader" in error_msg.lower():
                print(f"   ⚠️  HNSW索引错误: {e}")
                print("\n   解决方案:")
                print("   向量数据库索引损坏，需要重建:")
                print("   python -m e-commerce.init_knowledge_base --rebuild")
            else:
                print(f"   ⚠️  未知错误: {e}")
        
        print("\n" + "=" * 60)
        print("诊断完成")
        print("=" * 60)
        
    except ImportError as e:
        print(f"\n❌ 导入错误: {e}")
        print("\n请确保已安装必要的依赖:")
        print("pip install chromadb sentence-transformers")
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    check_vector_db()

