# AI Agent 快速开始指南

## 📋 项目条件评估

### ✅ 已具备的条件（90%）

1. **数据基础** ✅
   - 商品信息完整（名称、描述、价格、分类、库存等）
   - 评论系统完善（主评论、追评、评分、点赞数）
   - 购物车API已实现
   - 用户认证系统（JWT）

2. **技术基础** ✅
   - FastAPI框架
   - PostgreSQL数据库
   - Redis（可用于缓存）
   - 异步架构

3. **API接口** ✅
   - 商品查询接口
   - 评论查询接口
   - 购物车操作接口

### ⚠️ 需要新增的条件

1. **向量数据库** - 已实现（ChromaDB）
2. **Embedding模型** - 已实现（sentence-transformers）
3. **Langchain框架** - 已添加依赖
4. **Deepseek API** - 需要配置API Key

---

## 🚀 快速开始

### Step 1: 安装依赖

```bash
cd e-commerce
pip install -r requirements.txt
```

主要新增依赖：
- `langchain` - Agent框架
- `chromadb` - 向量数据库
- `sentence-transformers` - Embedding模型
- `openai` - Deepseek API客户端

### Step 2: 配置Deepseek API

在 `.env` 文件中添加：

```env
# Deepseek API配置
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
```

获取API Key：访问 https://platform.deepseek.com/

### Step 3: 构建知识库

```bash
# 初始化知识库（从数据库提取商品和评论，生成向量）
python init_knowledge_base.py

# 如果需要重建（删除旧数据）
python init_knowledge_base.py --rebuild
```

这个过程会：
1. 从数据库提取所有商品信息
2. 从数据库提取所有评论信息
3. 生成Embedding向量
4. 存储到ChromaDB向量数据库

### Step 4: 启动服务

```bash
# 启动FastAPI服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 5: 测试Agent接口

#### 1. 与Agent对话

```http
POST /agent/chat
Authorization: Bearer {token}
Content-Type: application/json

{
  "query": "帮我找性价比最高的手机，价格在2000-3000元之间"
}
```

响应：
```json
{
  "response": "我为您找到了3个相关商品。推荐：OPPO Find X8（3099元，评分4.5星，性价比分数0.85）...",
  "recommended_products": [
    {
      "id": 31,
      "name": "OPPO Find X8",
      "price": 3099.0,
      "rating": 4.5,
      "review_count": 10,
      "value_score": 0.85
    }
  ],
  "total_found": 3
}
```

#### 2. 获取推荐

```http
GET /agent/recommend?query=性价比最高的手机&max_results=5
Authorization: Bearer {token}
```

#### 3. Agent自动添加到购物车

```http
POST /agent/add-to-cart
Authorization: Bearer {token}
Content-Type: application/json

{
  "product_id": 31,
  "quantity": 1
}
```

---

## 📊 实现的功能

### 1. 知识库构建 ✅

- **数据提取**：从数据库提取商品和评论
- **文本处理**：构建知识文档
- **向量化**：使用sentence-transformers生成Embedding
- **存储**：存储到ChromaDB向量数据库

### 2. RAG检索 ✅

- **语义搜索**：使用向量相似度搜索
- **混合检索**：支持商品和评论的语义检索
- **结果排序**：按相关性排序

### 3. 智能推荐 ✅

- **性价比计算**：综合价格、评分、评论数、好评率
- **智能排序**：按性价比分数排序
- **自然语言回复**：使用Deepseek API生成友好回复

### 4. 购物车操作 ✅

- **自动添加**：Agent可以将推荐商品添加到购物车
- **权限验证**：确保用户只能操作自己的购物车

---

## 🎯 核心功能说明

### 性价比计算公式

```python
性价比分数 = (
    平均评分/5 * 0.4 +      # 评分权重40%
    价格优势 * 0.3 +         # 价格权重30%
    评论数量 * 0.2 +         # 评论数权重20%
    好评率 * 0.1             # 好评率权重10%
)
```

### RAG检索流程

1. 用户自然语言查询 → 2. 向量化查询 → 3. 语义搜索 → 4. 获取商品详情 → 5. 计算性价比 → 6. 排序推荐 → 7. 生成回复

---

## 📝 下一步优化

### 短期优化

1. **意图解析增强**
   - 使用Deepseek API进行更精确的意图识别
   - 提取价格范围、分类、评分要求等条件

2. **推荐算法优化**
   - 个性化推荐（基于用户历史）
   - 多维度排序（价格、评分、销量等）

3. **对话上下文**
   - 支持多轮对话
   - 记住用户偏好

### 长期优化

1. **完整Langchain Agent**
   - 使用Langchain的完整Agent框架
   - 实现工具链（Tool Chain）
   - 支持复杂工作流

2. **商家端智能上架**
   - 自动分类、标签、定价建议
   - AI生成商品描述

3. **性能优化**
   - 向量检索优化
   - 缓存策略
   - 批量处理

---

## ⚠️ 注意事项

1. **API成本**：Deepseek API调用会产生费用，注意控制调用频率
2. **向量数据库**：ChromaDB数据存储在本地 `chroma_db` 目录
3. **知识库更新**：新增商品/评论后需要更新知识库
4. **降级处理**：如果Deepseek API不可用，会使用简单回复

---

## 🔧 故障排查

### 问题1: 知识库构建失败

**原因**：数据库连接问题或模型不匹配

**解决**：
```bash
# 检查数据库连接
# 检查Product模型是否有category_id字段
# 如果没有，知识库服务会自动适配
```

### 问题2: Deepseek API调用失败

**原因**：API Key未配置或网络问题

**解决**：
- 检查 `.env` 文件中的 `DEEPSEEK_API_KEY`
- Agent会自动降级为简单回复

### 问题3: 向量搜索无结果

**原因**：知识库未构建或数据为空

**解决**：
```bash
# 重新构建知识库
python init_knowledge_base.py --rebuild
```

---

## 📚 相关文档

- `AGENT_IMPLEMENTATION_PLAN.md` - 详细实现计划
- `init_knowledge_base.py` - 知识库初始化脚本
- `app/agent/rag_agent.py` - Agent核心实现
- `app/services/vector_store_service.py` - 向量数据库服务

