# AI Agent 实现方案（RAG + Agent Workflow）

## 📊 项目条件评估

### ✅ 已具备的条件

1. **数据基础**
   - ✅ 商品信息完整（名称、描述、价格、分类、库存等）
   - ✅ 评论系统完善（主评论、追评、评分、点赞数）
   - ✅ 购物车API已实现（添加、查询、更新、删除）
   - ✅ 用户认证系统（JWT）
   - ✅ 分类系统（一级、二级分类）

2. **技术基础**
   - ✅ FastAPI框架（可扩展性好）
   - ✅ PostgreSQL数据库（结构化数据）
   - ✅ Redis（可用于缓存和会话）
   - ✅ 异步架构（适合AI Agent）

3. **API接口**
   - ✅ 商品查询接口（支持搜索、过滤、分页）
   - ✅ 评论查询接口
   - ✅ 购物车操作接口
   - ✅ 用户认证接口

### ⚠️ 需要新增的条件

1. **向量数据库**
   - ❌ 需要集成向量数据库（Milvus/ChromaDB/FAISS）
   - ❌ 需要Embedding模型（文本向量化）

2. **AI Agent框架**
   - ❌ 需要安装Langchain
   - ❌ 需要Deepseek API配置

3. **知识库构建**
   - ❌ 需要数据提取和预处理脚本
   - ❌ 需要Embedding生成和存储

---

## 🚀 实现步骤

### 阶段一：环境准备和依赖安装

#### 1.1 安装必要的Python包

```bash
pip install langchain langchain-community langchain-core
pip install langchain-openai  # 用于Deepseek API
pip install chromadb  # 或 milvus-client
pip install sentence-transformers  # 用于生成Embedding
pip install openai  # Deepseek兼容OpenAI API
```

#### 1.2 配置Deepseek API

在 `.env` 文件中添加：
```env
DEEPSEEK_API_KEY=your_deepseek_api_key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # 或使用Deepseek的embedding
```

---

### 阶段二：知识库构建（RAG基础）

#### 2.1 创建数据提取服务

**文件：** `app/services/knowledge_base_service.py`

功能：
- 从数据库提取所有商品信息
- 提取所有评论信息
- 将商品和评论组合成知识文档
- 数据清洗和格式化

#### 2.2 创建Embedding服务

**文件：** `app/services/embedding_service.py`

功能：
- 使用Embedding模型将文本转换为向量
- 支持批量处理
- 向量维度管理

#### 2.3 创建向量数据库服务

**文件：** `app/services/vector_store_service.py`

功能：
- 初始化向量数据库（ChromaDB/Milvus）
- 存储商品和评论的向量
- 实现语义搜索功能
- 支持增量更新

#### 2.4 创建知识库初始化脚本

**文件：** `init_knowledge_base.py`

功能：
- 一次性构建完整知识库
- 支持增量更新（新商品、新评论）
- 支持重建知识库

---

### 阶段三：Agent开发（Langchain + Deepseek）

#### 3.1 创建Agent工具（Tools）

**文件：** `app/agent/tools.py`

工具列表：
1. **search_products_tool** - 搜索商品（RAG检索）
2. **get_product_details_tool** - 获取商品详情
3. **add_to_cart_tool** - 添加到购物车
4. **compare_products_tool** - 比较商品
5. **filter_by_conditions_tool** - 条件过滤

#### 3.2 创建意图解析模块

**文件：** `app/agent/intent_parser.py`

功能：
- 使用Deepseek API解析用户自然语言
- 提取意图（搜索、比较、推荐等）
- 提取条件（价格范围、分类、评分等）
- 提取实体（商品名称、品牌等）

#### 3.3 创建RAG检索模块

**文件：** `app/agent/rag_retriever.py`

功能：
- 使用Langchain集成向量数据库
- 实现语义检索
- 支持多轮对话上下文
- 结果排序和过滤

#### 3.4 创建推荐引擎

**文件：** `app/agent/recommendation_engine.py`

功能：
- 计算性价比分数（价格、评分、评论数等）
- 多维度排序（价格、评分、销量等）
- 个性化推荐（基于用户历史）

#### 3.5 创建Agent主流程

**文件：** `app/agent/product_agent.py`

功能：
- 使用Langchain Agent框架
- 串联各个工具和模块
- 实现工作流编排
- 处理用户交互

---

### 阶段四：API接口开发

#### 4.1 创建Agent路由

**文件：** `app/routers/agent.py`

接口：
- `POST /agent/chat` - 与Agent对话
- `POST /agent/search` - 智能搜索商品
- `POST /agent/recommend` - 获取推荐商品
- `POST /agent/add-to-cart` - Agent自动添加到购物车

#### 4.2 创建知识库管理接口

**文件：** `app/routers/knowledge_base.py`

接口：
- `POST /knowledge-base/rebuild` - 重建知识库（管理员）
- `POST /knowledge-base/update` - 增量更新知识库
- `GET /knowledge-base/status` - 查看知识库状态

---

### 阶段五：工作流编排（MCP Workflow）

#### 5.1 定义Agent功能链

**文件：** `app/agent/workflow.py`

功能链：
1. **Parsing Chain** - 意图解析
2. **Retrieval Chain** - RAG检索
3. **Filtering Chain** - 条件过滤
4. **Recommendation Chain** - 推荐排序
5. **Generation Chain** - 生成响应
6. **Action Chain** - 执行操作（如添加到购物车）

#### 5.2 实现工作流编排

使用Langchain的SequentialChain或AgentExecutor实现：
- 用户查询 → 意图解析 → RAG检索 → 过滤排序 → 推荐 → 生成响应 → 执行操作

---

## 📋 详细实现计划

### Step 1: 安装依赖和配置

```bash
# 安装Langchain和相关库
pip install langchain langchain-community langchain-core langchain-openai
pip install chromadb  # 轻量级向量数据库
pip install sentence-transformers  # Embedding模型
pip install tiktoken  # Token计数
```

### Step 2: 创建知识库服务

需要实现：
- 数据提取（商品+评论）
- 文本分块（Chunking）
- Embedding生成
- 向量存储

### Step 3: 创建Agent工具

需要实现：
- RAG检索工具
- 商品查询工具
- 购物车操作工具
- 商品比较工具

### Step 4: 创建Agent主程序

使用Langchain的Agent框架：
- 定义工具列表
- 配置LLM（Deepseek）
- 创建Agent Executor
- 实现对话循环

### Step 5: 创建API接口

- Agent对话接口
- 知识库管理接口
- 监控和日志接口

---

## 🎯 核心功能实现要点

### 1. 性价比计算

```python
def calculate_value_score(product, reviews):
    """
    计算性价比分数
    分数 = (平均评分 * 0.4) + (价格优势 * 0.3) + (评论数量 * 0.2) + (好评率 * 0.1)
    """
    avg_rating = sum(r.rating for r in reviews) / len(reviews) if reviews else 0
    price_score = 1 / (product.price / 100)  # 价格越低分数越高
    review_count_score = min(len(reviews) / 10, 1)  # 评论数归一化
    positive_rate = sum(1 for r in reviews if r.rating >= 4) / len(reviews) if reviews else 0
    
    score = (avg_rating / 5 * 0.4) + (price_score * 0.3) + (review_count_score * 0.2) + (positive_rate * 0.1)
    return score
```

### 2. 自然语言查询解析

使用Deepseek API进行意图识别和实体提取：
- 意图：搜索、比较、推荐、询问
- 实体：商品名称、分类、价格范围
- 条件：评分要求、库存要求、商家要求

### 3. RAG检索策略

- 混合检索：语义检索 + 关键词检索
- 重排序：使用LLM对检索结果重排序
- 上下文增强：结合用户历史、购物车内容

---

## 📝 下一步行动

1. **立即开始**：安装依赖，配置Deepseek API
2. **第一阶段**：构建知识库（数据提取、Embedding、向量存储）
3. **第二阶段**：开发Agent工具和RAG检索
4. **第三阶段**：实现Agent主流程和工作流
5. **第四阶段**：创建API接口和测试

---

## ⚠️ 注意事项

1. **数据隐私**：确保用户数据安全
2. **API成本**：Deepseek API调用需要控制成本
3. **性能优化**：向量检索和LLM调用需要优化
4. **错误处理**：Agent失败时的降级策略
5. **用户体验**：响应时间、交互流畅度

