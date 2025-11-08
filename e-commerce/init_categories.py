"""
初始化商品分类数据
创建一级和二级分类
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.models.category import Category


async def init_categories():
    """初始化分类数据"""
    async for db in get_db():
        try:
            # 检查是否已有分类
            from sqlalchemy.future import select
            existing = await db.execute(select(Category))
            if existing.scalars().first():
                print("Categories already exist. Skipping initialization.")
                return
            
            # 一级分类
            categories_data = [
                # 电子产品
                {"name": "电子产品", "description": "各类电子设备", "level": 1, "parent_id": None},
                # 服装服饰
                {"name": "服装服饰", "description": "各类服装和配饰", "level": 1, "parent_id": None},
                # 家居用品
                {"name": "家居用品", "description": "家居装饰和生活用品", "level": 1, "parent_id": None},
                # 图书文教
                {"name": "图书文教", "description": "图书和教育用品", "level": 1, "parent_id": None},
                # 美妆护肤
                {"name": "美妆护肤", "description": "化妆品和护肤品", "level": 1, "parent_id": None},
                # 运动户外
                {"name": "运动户外", "description": "运动装备和户外用品", "level": 1, "parent_id": None},
                # 食品饮料
                {"name": "食品饮料", "description": "各类食品和饮料", "level": 1, "parent_id": None},
                # 汽车用品
                {"name": "汽车用品", "description": "汽车配件和用品", "level": 1, "parent_id": None},
            ]
            
            # 创建一级分类
            level1_categories = {}
            for cat_data in categories_data:
                category = Category(**cat_data)
                db.add(category)
                await db.flush()  # 获取ID
                level1_categories[cat_data["name"]] = category.id
            
            # 二级分类
            level2_categories_data = [
                # 电子产品的二级分类
                {"name": "手机", "description": "智能手机", "level": 2, "parent_id": level1_categories["电子产品"]},
                {"name": "电脑", "description": "笔记本电脑和台式机", "level": 2, "parent_id": level1_categories["电子产品"]},
                {"name": "平板", "description": "平板电脑", "level": 2, "parent_id": level1_categories["电子产品"]},
                {"name": "耳机", "description": "各类耳机", "level": 2, "parent_id": level1_categories["电子产品"]},
                {"name": "智能手表", "description": "智能手表和手环", "level": 2, "parent_id": level1_categories["电子产品"]},
                
                # 服装服饰的二级分类
                {"name": "男装", "description": "男士服装", "level": 2, "parent_id": level1_categories["服装服饰"]},
                {"name": "女装", "description": "女士服装", "level": 2, "parent_id": level1_categories["服装服饰"]},
                {"name": "童装", "description": "儿童服装", "level": 2, "parent_id": level1_categories["服装服饰"]},
                {"name": "鞋靴", "description": "各类鞋靴", "level": 2, "parent_id": level1_categories["服装服饰"]},
                {"name": "箱包", "description": "箱包和配饰", "level": 2, "parent_id": level1_categories["服装服饰"]},
                
                # 家居用品的二级分类
                {"name": "家具", "description": "各类家具", "level": 2, "parent_id": level1_categories["家居用品"]},
                {"name": "家纺", "description": "床上用品和纺织品", "level": 2, "parent_id": level1_categories["家居用品"]},
                {"name": "厨具", "description": "厨房用品", "level": 2, "parent_id": level1_categories["家居用品"]},
                {"name": "装饰", "description": "家居装饰品", "level": 2, "parent_id": level1_categories["家居用品"]},
                
                # 图书文教的二级分类
                {"name": "图书", "description": "各类图书", "level": 2, "parent_id": level1_categories["图书文教"]},
                {"name": "文具", "description": "办公文具", "level": 2, "parent_id": level1_categories["图书文教"]},
                {"name": "教具", "description": "教学用具", "level": 2, "parent_id": level1_categories["图书文教"]},
            ]
            
            # 创建二级分类
            for cat_data in level2_categories_data:
                category = Category(**cat_data)
                db.add(category)
            
            await db.commit()
            print("Categories initialized successfully!")
            
        except Exception as e:
            await db.rollback()
            print(f"Error initializing categories: {e}")
            raise
        finally:
            break


if __name__ == "__main__":
    asyncio.run(init_categories())

