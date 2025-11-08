"""
Embedding服务
用于将文本转换为向量
"""
from typing import List
import os
from sentence_transformers import SentenceTransformer
import numpy as np


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
            # 使用默认模型
            self.model = SentenceTransformer("all-MiniLM-L6-v2")
    
    def encode(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        将文本列表转换为向量
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小
        
        Returns:
            np.ndarray: 向量数组，形状为 (len(texts), embedding_dim)
        """
        if not texts:
            return np.array([])
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_numpy=True
        )
        
        return embeddings
    
    def encode_single(self, text: str) -> np.ndarray:
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

