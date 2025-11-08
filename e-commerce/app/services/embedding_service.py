"""
Embedding服务
用于将文本转换为向量
"""
from typing import List, Optional
import os

# 可选导入sentence_transformers，如果未安装或PyTorch DLL加载失败则提供友好的错误提示
try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    SENTENCE_TRANSFORMERS_AVAILABLE = True
    IMPORT_ERROR = None
except (ImportError, OSError) as e:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None
    np = None
    IMPORT_ERROR = str(e)


class EmbeddingService:
    """
    Embedding服务
    使用sentence-transformers生成文本向量
    """
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        初始化Embedding服务
        
        Args:
            model_name: Embedding模型名称
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                f"sentence-transformers is not available: {IMPORT_ERROR}. "
                "Please install it with: pip install sentence-transformers"
            )
        
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """加载Embedding模型"""
        try:
            self.model = SentenceTransformer(self.model_name)
            print(f"Embedding模型加载成功: {self.model_name}")
        except Exception as e:
            print(f"加载Embedding模型失败: {e}")
            # 尝试使用默认模型
            try:
                self.model = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as e2:
                raise ImportError(
                    f"无法加载Embedding模型: {e2}. "
                    "请检查sentence-transformers和PyTorch是否正确安装。"
                )
    
    def encode(self, texts: List[str], batch_size: int = 32):
        """
        将文本列表转换为向量
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
        
        Returns:
            np.ndarray: 向量数组，形状为 (len(texts), embedding_dim)
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("sentence-transformers is not available")
        
        if not texts:
            return np.array([])
        
        if self.model is None:
            raise RuntimeError("Embedding模型未加载")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def encode_single(self, text: str):
        """
        将单个文本转换为向量
        
        Args:
            text: 文本字符串
        
        Returns:
            np.ndarray: 向量，形状为 (embedding_dim,)
        """
        return self.encode([text])[0]
    
    @property
    def embedding_dim(self) -> int:
        """获取向量维度"""
        if self.model is None:
            return 384  # all-MiniLM-L6-v2的默认维度
        return self.model.get_sentence_embedding_dimension()

