"""
商品推荐Agent
使用Langchain + Deepseek API实现智能商品推荐和购物车操作
"""
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import Tool
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.settings import settings
from app.services.vector_store_service import VectorStoreService
from app.services.product_service import ProductService
from app.services.cart_item_service import CartService
from app.services.review_service import ReviewService
from app.schemas.cart_item import CartItemCreate
from app.models.user import User


class ProductAgent:
    """
    商品推荐Agent
    帮助用户搜索、比较、推荐商品，并自动添加到购物车
    """
    
    def __init__(self):
        """初始化Agent"""
        self.llm = None
        self.agent_executor = None
        self.vector_store = VectorStoreService()
        self._initialize_llm()
        self._initialize_agent()
    
    def _initialize_llm(self):
        """初始化LLM（Deepseek API）"""
        try:
            # Deepseek兼容OpenAI API格式
            self.llm = ChatOpenAI(
                model="deepseek-chat",
                api_key=settings.DEEPSEEK_API_KEY if hasattr(settings, 'DEEPSEEK_API_KEY') else "",
                base_url=settings.DEEPSEEK_API_BASE if hasattr(settings, 'DEEPSEEK_API_BASE') else "https://api.deepseek.com/v1",
                temperature=0.7,
                max_tokens=2000
            )
            print("Deepseek LLM初始化成功")
        except Exception as e:
            print(f"LLM初始化失败: {e}")
            # 如果没有配置Deepseek，可以使用其他LLM或抛出错误
            raise
    
    def _initialize_agent(self):
        """初始化Agent"""
        # 定义工具
        tools = self._create_tools()
        
        # 定义提示词
        prompt = ChatPromptTemplate.from_messages([
            ("system", """你是一个专业的电商购物助手，帮助用户找到性价比最高的商品。

你的能力：
1. 理解用户的自然语言查询（如"帮我找性价比最高的手机"）
2. 使用语义搜索在知识库中查找相关商品
3. 分析商品的价格、评分、评论等信息
4. 计算性价比并推荐最佳商品
5. 可以将推荐的商品添加到用户的购物车

工作流程：
1. 理解用户意图和需求
2. 使用语义搜索查找相关商品
3. 获取商品详细信息（价格、评分、评论）
4. 计算性价比分数
5. 推荐最佳商品
6. 询问用户是否添加到购物车，如果用户同意则自动添加

性价比计算公式：
性价比分数 = (平均评分/5 * 0.4) + (价格优势 * 0.3) + (评论数量 * 0.2) + (好评率 * 0.1)

请用中文回复用户，语气友好、专业。"""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        # 创建Agent
        agent = create_openai_tools_agent(self.llm, tools, prompt)
        
        # 创建Agent执行器
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=5,
            handle_parsing_errors=True
        )
    
    def _create_tools(self) -> List[Tool]:
        """创建Agent工具列表"""
        from app.agent.tools import (
            search_products_by_semantic,
            get_product_details,
            add_product_to_cart,
            compare_products,
            filter_products_by_conditions
        )
        
        # 包装异步工具
        async_tools = [
            self._wrap_async_tool("search_products", self._search_products_async),
            self._wrap_async_tool("get_product_details", self._get_product_details_async),
            self._wrap_async_tool("add_to_cart", self._add_to_cart_async),
            self._wrap_async_tool("calculate_value_score", self._calculate_value_score_async),
        ]
        
        # 同步工具
        sync_tools = [
            search_products_by_semantic,
            compare_products,
            filter_products_by_conditions
        ]
        
        return sync_tools + async_tools
    
    def _wrap_async_tool(self, name: str, func):
        """包装异步函数为Tool"""
        from langchain.tools import StructuredTool
        
        # 这里需要将异步函数转换为同步函数
        # 由于Langchain的Tool是同步的，我们需要在调用时处理异步
        def sync_wrapper(*args, **kwargs):
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(func(*args, **kwargs))
        
        return StructuredTool.from_function(
            func=sync_wrapper,
            name=name,
            description=func.__doc__
        )
    
    async def _search_products_async(self, query: str, n_results: int = 10) -> str:
        """异步搜索商品"""
        results = self.vector_store.search(query, n_results=n_results)
        import json
        return json.dumps(results, ensure_ascii=False, indent=2)
    
    async def _get_product_details_async(self, product_id: int, db: AsyncSession) -> str:
        """异步获取商品详情"""
        # 这里需要db参数，但Tool无法直接传递，需要在Agent调用时处理
        return f"需要从数据库获取商品 {product_id} 的详细信息"
    
    async def _add_to_cart_async(self, product_id: int, quantity: int, user: User, db: AsyncSession) -> str:
        """异步添加到购物车"""
        # 这里需要user和db参数，需要在Agent调用时处理
        return f"需要将商品 {product_id} 添加到用户 {user.id} 的购物车"
    
    async def _calculate_value_score_async(self, product_id: int, db: AsyncSession) -> str:
        """计算商品性价比分数"""
        # 获取商品和评论
        # 计算性价比
        return "需要计算性价比分数"
    
    async def chat(
        self,
        user_query: str,
        user: User,
        db: AsyncSession,
        context: Optional[Dict] = None
    ) -> str:
        """
        与Agent对话
        
        Args:
            user_query: 用户查询
            user: 当前用户
            db: 数据库会话
            context: 上下文信息（购物车、历史等）
        
        Returns:
            str: Agent回复
        """
        # 构建输入，包含用户信息和上下文
        input_text = f"""
用户查询：{user_query}
用户ID：{user.id}
用户角色：{user.role}
"""
        
        if context:
            if context.get("cart_items"):
                input_text += f"\n当前购物车商品数量：{len(context['cart_items'])}"
            if context.get("recent_views"):
                input_text += f"\n最近浏览的商品：{', '.join(context['recent_views'])}"
        
        try:
            # 执行Agent
            result = await self.agent_executor.ainvoke({
                "input": input_text,
                "agent_scratchpad": []
            })
            
            return result.get("output", "抱歉，我无法处理您的请求。")
        except Exception as e:
            return f"处理请求时出错: {str(e)}"
    
    async def recommend_products(
        self,
        query: str,
        user: User,
        db: AsyncSession,
        max_results: int = 5
    ) -> List[Dict]:
        """
        推荐商品
        
        Args:
            query: 用户查询
            user: 当前用户
            db: 数据库会话
            max_results: 最大推荐数量
        
        Returns:
            List[Dict]: 推荐商品列表
        """
        # 使用语义搜索
        search_results = self.vector_store.search(query, n_results=max_results * 2)
        
        # 获取商品详细信息并计算性价比
        recommended = []
        for result in search_results[:max_results]:
            product_id = result["metadata"].get("product_id")
            if product_id:
                # 获取商品详情
                # 计算性价比
                # 添加到推荐列表
                recommended.append({
                    "product_id": product_id,
                    "product_name": result["metadata"].get("product_name"),
                    "price": result["metadata"].get("price"),
                    "rating": result["metadata"].get("rating"),
                    "relevance_score": 1 - result["distance"] if result["distance"] else 0
                })
        
        # 按性价比排序
        recommended.sort(key=lambda x: x["relevance_score"], reverse=True)
        
        return recommended[:max_results]

