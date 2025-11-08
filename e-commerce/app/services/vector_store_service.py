"""
向量数据库服务
使用ChromaDB存储和检索向量
"""
from typing import List, Dict, Optional
import os

# 可选导入chromadb，如果未安装则提供友好的错误提示
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    Settings = None

try:
    from app.services.embedding_service import EmbeddingService
    EMBEDDING_AVAILABLE = True
    EMBEDDING_ERROR = None
except (ImportError, OSError) as e:
    EMBEDDING_AVAILABLE = False
    EMBEDDING_ERROR = str(e)
    EmbeddingService = None


class VectorStoreService:
    """
    向量数据库服务
    使用ChromaDB存储商品和评论的向量
    """
    
    def __init__(self, persist_directory: str = "chroma_db", collection_name: str = "ecommerce_knowledge"):
        """
        初始化向量数据库服务
        
        Args:
            persist_directory: 持久化目录
            collection_name: 集合名称
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError(
                "chromadb is not installed. Please install it with: pip install chromadb"
            )
        if not EMBEDDING_AVAILABLE:
            error_msg = EMBEDDING_ERROR if EMBEDDING_ERROR else 'Unknown error (可能是PyTorch DLL加载失败)'
            raise ImportError(
                f"EmbeddingService is not available: {error_msg}. "
                "Please install sentence-transformers and PyTorch: "
                "pip install sentence-transformers torch"
            )
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        # 延迟加载EmbeddingService，避免在导入时就加载PyTorch
        self._embedding_service = None
        self._initialize_client()
    
    @property
    def embedding_service(self):
        """延迟加载EmbeddingService"""
        if self._embedding_service is None:
            try:
                self._embedding_service = EmbeddingService()
            except (ImportError, RuntimeError, OSError) as e:
                raise ImportError(
                    f"无法初始化EmbeddingService: {e}. "
                    "请检查sentence-transformers和PyTorch是否正确安装。"
                )
        return self._embedding_service
    
    def _initialize_client(self):
        """初始化ChromaDB客户端"""
        try:
            # 创建持久化目录
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # 初始化ChromaDB客户端
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # 获取或创建集合
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "E-commerce product and review knowledge base"}
            )
            
            print(f"向量数据库初始化成功: {self.collection_name}")
        except Exception as e:
            print(f"初始化向量数据库失败: {e}")
            raise
    
    def add_documents(self, documents: List[Dict], batch_size: int = 100):
        """
        添加文档到向量数据库
        
        Args:
            documents: 文档列表，每个文档包含 text, id, metadata
            batch_size: 批处理大小
        """
        if not documents:
            return
        
        # 提取文本
        texts = [doc.get("text", "") for doc in documents]
        
        # 生成向量
        print(f"正在生成 {len(texts)} 个文档的向量...")
        embeddings = self.embedding_service.encode(texts, batch_size=batch_size)
        
        # 准备数据
        ids = [str(doc["id"]) for doc in documents]
        metadatas = [
            {
                "type": doc.get("type", "unknown"),
                "product_id": doc.get("product_id", doc.get("id")),
                "product_name": doc.get("product_name", doc.get("name", "")),
                "price": doc.get("price", 0),
                "rating": doc.get("rating", 0),
                "category": doc.get("category", ""),
            }
            for doc in documents
        ]
        
        # 批量添加
        for i in range(0, len(documents), batch_size):
            batch_ids = ids[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size].tolist()
            batch_texts = texts[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            
            self.collection.add(
                ids=batch_ids,
                embeddings=batch_embeddings,
                documents=batch_texts,
                metadatas=batch_metadatas
            )
            print(f"已添加 {i+len(batch_ids)}/{len(documents)} 个文档")
        
        print(f"成功添加 {len(documents)} 个文档到向量数据库")
    
    def search(self, query: str, n_results: int = 10, filter_dict: Optional[Dict] = None) -> List[Dict]:
        """
        语义搜索
        
        Args:
            query: 查询文本
            n_results: 返回结果数量
            filter_dict: 过滤条件（ChromaDB格式）
        
        Returns:
            List[Dict]: 搜索结果列表
        """
        # 生成查询向量
        query_embedding = self.embedding_service.encode_single(query)
        
        # 执行搜索
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=n_results,
            where=filter_dict
        )
        
        # 格式化结果
        formatted_results = []
        if results["ids"] and len(results["ids"][0]) > 0:
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None
                })
        
        return formatted_results
    
    def delete_collection(self):
        """删除集合（用于重建）"""
        try:
            self.client.delete_collection(name=self.collection_name)
            print(f"已删除集合: {self.collection_name}")
        except Exception as e:
            print(f"删除集合失败: {e}")
    
    def get_collection_info(self) -> Dict:
        """获取集合信息"""
        try:
            count = self.collection.count()
            return {
                "name": self.collection_name,
                "count": count,
                "status": "active"
            }
        except Exception as e:
            return {
                "name": self.collection_name,
                "count": 0,
                "status": f"error: {str(e)}"
            }

