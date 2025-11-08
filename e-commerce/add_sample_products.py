"""
快速添加示例商品数据
运行方式：python add_sample_products.py
"""
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database.session import AsyncSessionLocal
from app.models.product import Product
from app.models.user import User
from app.models.category import Category
from app.schemas.user import Role


async def get_first_vendor_or_admin():
    """获取第一个商家或管理员用户ID"""
    async with AsyncSessionLocal() as db:
        # 先查找商家
        result = await db.execute(
            select(User).where(User.role == Role.vendor).limit(1)
        )
        vendor = result.scalar_one_or_none()
        
        if vendor:
            return vendor.id
        
        # 如果没有商家，查找管理员
        result = await db.execute(
            select(User).where(User.role == Role.admin).limit(1)
        )
        admin = result.scalar_one_or_none()
        
        if admin:
            return admin.id
        
        # 如果都没有，返回第一个用户
        result = await db.execute(select(User).limit(1))
        first_user = result.scalar_one_or_none()
        
        if first_user:
            return first_user.id
        
        return None


async def get_category_ids(db: AsyncSession):
    """获取各个分类的ID"""
    # 获取分类ID映射
    result = await db.execute(select(Category).where(Category.parent_id.is_(None)))
    categories = result.scalars().all()
    
    category_map = {}
    for cat in categories:
        if '电子' in cat.name:
            category_map['electronics'] = cat.id
        elif '服装' in cat.name or '鞋包' in cat.name:
            category_map['fashion'] = cat.id
        elif '家居' in cat.name:
            category_map['home'] = cat.id
        elif '图书' in cat.name:
            category_map['books'] = cat.id
    
    return category_map


async def clear_all_products():
    """清空所有商品"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Product))
        existing = result.scalars().all()
        
        if existing:
            print(f"正在删除 {len(existing)} 个商品...")
            for product in existing:
                await db.delete(product)
            await db.commit()
            print(f"[成功] 已删除 {len(existing)} 个商品")
        else:
            print("数据库中没有商品")


async def add_sample_products():
    """添加示例商品"""
    import random
    
    # 获取vendor_id
    vendor_id = await get_first_vendor_or_admin()
    
    if not vendor_id:
        print("[错误] 错误：数据库中没有用户！")
        print("请先注册一个用户（建议选择'商家'角色）")
        return
    
    print(f"[成功] 使用用户ID: {vendor_id} 作为商品供应商")
    
    async with AsyncSessionLocal() as db:
        # 获取分类ID
        category_ids = await get_category_ids(db)
        
        if not category_ids:
            print("[错误] 错误：数据库中没有分类！")
            print("请先运行分类初始化脚本：python init_categories.py")
            return
        
        print(f"[成功] 找到 {len(category_ids)} 个分类")
        
        # 检查是否已有商品
        result = await db.execute(select(Product))
        existing = result.scalars().all()
        
        if existing:
            print(f"[警告] 数据库中已有 {len(existing)} 个商品")
            print("[操作] 自动清空现有商品...")
            await clear_all_products()
        
        # 生成200个商品数据
        products = []
        
        # ==================== 电子产品 (60个) ====================
        # 手机 (30个) - 包含各个品牌和价位
        phones = [
            # iPhone系列
            ("iPhone 15 Pro Max", "Apple A17 Pro芯片，6.7英寸超视网膜XDR显示屏，120Hz自适应刷新率，钛金属设计，三摄系统，支持5G", 9999.00),
            ("iPhone 15 Pro", "Apple A17 Pro芯片，6.1英寸超视网膜XDR显示屏，120Hz自适应刷新率，钛金属设计，三摄系统", 8999.00),
            ("iPhone 15 Plus", "Apple A16芯片，6.7英寸超视网膜XDR显示屏，双摄系统，超长续航", 7999.00),
            ("iPhone 15", "Apple A16芯片，6.1英寸超视网膜XDR显示屏，双摄系统，动态岛设计", 6999.00),
            ("iPhone 14 Pro", "Apple A16芯片，6.1英寸超视网膜XDR显示屏，120Hz自适应刷新率，灵动岛", 7999.00),
            
            # 华为系列
            ("华为Mate 60 Pro", "麒麟9000S芯片，6.82英寸OLED曲面屏，5000mAh电池，88W超级快充，卫星通信", 6999.00),
            ("华为P60 Pro", "骁龙8+ Gen 1芯片，6.67英寸OLED曲面屏，4815mAh电池，88W超级快充，徕卡影像", 5999.00),
            ("华为nova 12 Pro", "麒麟9000SL芯片，6.76英寸OLED曲面屏，4600mAh电池，100W快充", 3999.00),
            
            # 小米系列
            ("小米14 Pro", "骁龙8 Gen 3芯片，6.73英寸2K AMOLED屏，5000mAh电池，120W快充，徕卡光学镜头", 4999.00),
            ("小米14", "骁龙8 Gen 3芯片，6.36英寸AMOLED屏，4610mAh电池，90W快充，徕卡光学镜头", 3999.00),
            ("小米13 Ultra", "骁龙8 Gen 2芯片，6.73英寸2K AMOLED屏，5000mAh电池，90W快充，徕卡专业光学", 5999.00),
            ("Redmi K70 Pro", "骁龙8 Gen 3芯片，6.67英寸2K OLED屏，5000mAh电池，120W快充", 2999.00),
            ("Redmi Note 13 Pro", "骁龙7s Gen 2芯片，6.67英寸OLED屏，5100mAh电池，67W快充", 1699.00),
            
            # OPPO系列（重点）
            ("OPPO Find X7 Ultra", "骁龙8 Gen 3芯片，6.82英寸2K AMOLED屏，5000mAh电池，100W超级闪充，哈苏影像", 5999.00),
            ("OPPO Find X7 Pro", "天玑9300芯片，6.78英寸2K AMOLED屏，5000mAh电池，100W超级闪充，哈苏影像", 4999.00),
            ("OPPO Find X7", "天玑9300芯片，6.7英寸AMOLED屏，5000mAh电池，100W超级闪充", 3999.00),
            ("OPPO Find N3", "骁龙8 Gen 2芯片，7.82英寸内屏，120Hz刷新率，折叠屏旗舰，哈苏影像系统", 8999.00),
            ("OPPO Reno11 Pro", "天玑8200芯片，6.74英寸AMOLED曲面屏，4700mAh电池，80W闪充，轻薄设计", 3299.00),
            ("OPPO Reno11", "天玑8100芯片，6.7英寸AMOLED屏，4800mAh电池，67W闪充", 2699.00),
            ("OPPO K12", "骁龙7 Gen 3芯片，6.7英寸AMOLED屏，5500mAh大电池，100W快充，性价比之选", 1999.00),
            ("OPPO A2 Pro", "天玑7050芯片，6.7英寸AMOLED屏，5000mAh电池，67W快充，超薄机身", 1699.00),
            
            # vivo系列
            ("vivo X100 Pro", "天玑9300芯片，6.78英寸2K AMOLED屏，5400mAh电池，120W快充，蔡司光学", 5499.00),
            ("vivo X100", "天玑9300芯片，6.78英寸AMOLED屏，5000mAh电池，120W快充，蔡司光学", 4299.00),
            ("vivo S18 Pro", "天玑9200+芯片，6.78英寸AMOLED曲面屏，5000mAh电池，80W快充，轻薄设计", 3299.00),
            ("iQOO 12 Pro", "骁龙8 Gen 3芯片，6.78英寸2K AMOLED屏，5100mAh电池，120W快充，电竞性能", 4999.00),
            
            # 三星系列
            ("Samsung Galaxy S24 Ultra", "骁龙8 Gen 3芯片，6.8英寸2K AMOLED屏，5000mAh电池，45W快充，S Pen", 9999.00),
            ("Samsung Galaxy S24+", "骁龙8 Gen 3芯片，6.7英寸2K AMOLED屏，4900mAh电池，45W快充", 7999.00),
            ("Samsung Galaxy Z Fold5", "骁龙8 Gen 2芯片，7.6英寸内屏，120Hz刷新率，折叠屏旗舰", 13999.00),
            
            # 荣耀系列
            ("荣耀Magic6 Pro", "骁龙8 Gen 3芯片，6.8英寸OLED曲面屏，5600mAh电池，80W快充，荣耀鹰眼相机", 5699.00),
            ("荣耀100 Pro", "骁龙8 Gen 2芯片，6.78英寸OLED曲面屏，5000mAh电池，100W快充", 3299.00),
        ]
        
        for name, desc, price in phones:
            products.append(Product(
                name=name,
                description=desc,
                price=price,
                stock=random.randint(20, 100),
                category_id=category_ids.get('electronics'),
                vendor_id=vendor_id,
                is_active=True,
                image_url="https://images.unsplash.com/photo-1592286927505-4ffd2560e4c8?w=400"
            ))
        
        # 笔记本电脑 (15个)
        laptops = [
            ("MacBook Pro 16英寸 M3 Max", "M3 Max芯片，36GB统一内存，1TB SSD，16.2英寸Liquid Retina XDR显示屏，专业级性能", 25999.00),
            ("MacBook Pro 14英寸 M3 Pro", "M3 Pro芯片，18GB统一内存，512GB SSD，14.2英寸Liquid Retina XDR显示屏", 18999.00),
            ("MacBook Air 15英寸 M3", "M3芯片，16GB统一内存，512GB SSD，15.3英寸Liquid Retina显示屏，超轻薄", 12999.00),
            ("MacBook Air 13英寸 M2", "M2芯片，8GB统一内存，256GB SSD，13.6英寸Liquid Retina显示屏", 9999.00),
            ("华为MateBook X Pro", "Intel Core i7-13700H，16GB内存，1TB SSD，14.2英寸3.1K触控屏", 9999.00),
            ("联想ThinkPad X1 Carbon", "Intel Core i7-1365U，16GB内存，512GB SSD，14英寸2.8K OLED屏，商务旗舰", 11999.00),
            ("戴尔XPS 15", "Intel Core i7-13700H，32GB内存，1TB SSD，15.6英寸4K OLED触控屏，创作者首选", 15999.00),
            ("华硕ROG魔霸新锐", "AMD Ryzen 9 7945HX，RTX 4070，32GB内存，1TB SSD，15.6英寸2.5K 240Hz电竞屏", 12999.00),
            ("小米笔记本Pro 14", "Intel Core i7-13700H，16GB内存，512GB SSD，14.5英寸2.8K OLED屏", 5999.00),
            ("荣耀MagicBook X 16 Pro", "Intel Core i5-13500H，16GB内存，512GB SSD，16英寸全面屏", 4999.00),
            ("联想小新Pro 16", "AMD Ryzen 7 7840H，16GB内存，1TB SSD，16英寸2.5K 120Hz屏", 5999.00),
            ("惠普战66六代", "Intel Core i5-1340P，16GB内存，512GB SSD，14英寸屏，商务办公", 5499.00),
            ("神舟战神Z8", "Intel Core i7-13650HX，RTX 4060，16GB内存，512GB SSD，游戏本性价比之选", 6999.00),
            ("机械革命极光Pro", "Intel Core i7-13700H，RTX 4060，32GB内存，1TB SSD，16英寸2.5K屏", 7999.00),
            ("微软Surface Laptop 5", "Intel Core i7-1255U，16GB内存，512GB SSD，13.5英寸PixelSense触控屏", 10999.00),
        ]
        
        for name, desc, price in laptops:
            products.append(Product(
                name=name,
                description=desc,
                price=price,
                stock=random.randint(10, 50),
                category_id=category_ids.get('electronics'),
                vendor_id=vendor_id,
                is_active=True,
                image_url="https://images.unsplash.com/photo-1517336714731-489689fd1ca8?w=400"
            ))
        
        # 其他电子产品 (15个)
        other_electronics = [
            ("iPad Pro 12.9英寸 M2", "M2芯片，8GB内存，256GB存储，12.9英寸Liquid Retina XDR显示屏，支持Apple Pencil", 7999.00),
            ("华为MatePad Pro 13.2", "麒麟9000S芯片，8GB内存，256GB存储，13.2英寸OLED屏，PC级应用生态", 5999.00),
            ("Sony WH-1000XM5 降噪耳机", "顶级降噪效果，30小时续航，LDAC高清音频，多点连接，自适应声音控制", 2699.00),
            ("AirPods Pro 2代", "主动降噪，空间音频，自适应通透模式，MagSafe充电，30小时续航", 1899.00),
            ("Apple Watch Ultra 2", "钛金属表壳，49mm表盘，S9芯片，双频GPS，100米防水，极限运动专用", 6299.00),
            ("华为Watch GT 4", "1.43英寸AMOLED屏，14天长续航，100+运动模式，血氧心率监测", 1488.00),
            ("DJI Mini 4 Pro", "4K 60fps视频，全向避障，34分钟续航，249克轻量化设计，航拍入门之选", 4788.00),
            ("GoPro HERO 12 Black", "5.3K 60fps视频，超强防抖，10米防水，HDR拍摄，运动相机标杆", 3498.00),
            ("Sony A7M4 微单相机", "3300万像素全画幅传感器，693点对焦，4K 60p视频，5轴防抖，专业摄影", 18999.00),
            ("Canon EOS R6 Mark II", "2420万像素全画幅传感器，40fps连拍，6K超采样4K视频，5轴防抖", 16999.00),
            ("索尼WF-1000XM5 真无线降噪耳机", "顶级降噪，24小时续航，LDAC高清音频，小巧舒适", 2299.00),
            ("Bose QuietComfort 45", "卓越降噪，24小时续航，轻量化设计，舒适佩戴", 2299.00),
            ("罗技MX Master 3S 鼠标", "无线办公鼠标，8000DPI，静音按键，多设备切换，人体工学设计", 799.00),
            ("Kindle Paperwhite 5", "6.8英寸电子墨水屏，防水设计，长续航，海量图书资源", 998.00),
            ("小米手环8 Pro", "1.74英寸AMOLED屏，150+运动模式，14天续航，血氧心率监测", 399.00),
        ]
        
        for name, desc, price in other_electronics:
            products.append(Product(
                name=name,
                description=desc,
                price=price,
                stock=random.randint(30, 150),
                category_id=category_ids.get('electronics'),
                vendor_id=vendor_id,
                is_active=True,
                image_url="https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=400"
            ))
        
        # ==================== 服装鞋包 (50个) ====================
        fashion_items = [
            # 运动鞋 (15个)
            ("Nike Air Jordan 1 黑红配色", "经典AJ1复刻款，优质皮革，黑红熊猫配色，限量发售，球鞋收藏必备", 1399.00),
            ("Nike Air Max 270", "270度气垫，舒适缓震，透气鞋面，日常百搭运动鞋", 899.00),
            ("Adidas Ultraboost 23", "Boost中底能量回弹，大陆马牌橡胶外底，跑步首选", 1299.00),
            ("Adidas Yeezy 350 V2", "椰子鞋经典款，Boost缓震，Primeknit编织鞋面，潮流单品", 1899.00),
            ("New Balance 990v6", "美产复古跑鞋，ENCAP缓震科技，麂皮鞋面，总统慢跑鞋", 1599.00),
            ("Asics Gel-Kayano 30", "GEL缓震胶，稳定支撑，专业跑鞋，马拉松训练必备", 1299.00),
            ("匹克态极闪现", "态极科技中底，轻质缓震，国产篮球鞋代表作", 499.00),
            ("李宁韦德之道10", "李宁云缓震，碳板支撑，实战篮球鞋，性价比高", 699.00),
            ("安踏KT8 汤普森战靴", "A-FLASHFOAM中底，透气鞋面，实战篮球鞋", 599.00),
            ("Converse Chuck 70 帆布鞋", "经典高帮帆布鞋，复古设计，百搭休闲", 499.00),
            ("Vans Old Skool", "经典滑板鞋，侧边条纹，帆布+麂皮拼接，街头潮流", 459.00),
            ("彪马Suede Classic", "麂皮经典款，复古运动鞋，简约百搭", 499.00),
            ("斯凯奇熊猫鞋", "轻质缓震，一脚蹬设计，舒适休闲鞋", 399.00),
            ("回力帆布鞋经典款", "国民帆布鞋，轻便透气，性价比之王", 59.00),
            ("飞跃帆布鞋", "法国经典款，轻便舒适，复古时尚", 79.00),
            
            # 服装 (20个)
            ("优衣库羽绒服", "90%白鸭绒，轻薄保暖，防风防水，多色可选", 799.00),
            ("The North Face冲锋衣", "GORE-TEX面料，防水透气，三合一设计，户外必备", 2299.00),
            ("始祖鸟Alpha SV冲锋衣", "顶级GORE-TEX Pro，极限防护，专业登山装备", 5999.00),
            ("Canada Goose大鹅羽绒服", "625蓬松度白鸭绒，加拿大制造，极寒御寒神器", 8999.00),
            ("波司登登峰系列羽绒服", "90%白鹅绒，充绒量300g，防寒保暖，国产高端羽绒服", 2999.00),
            ("Levi's 501经典牛仔裤", "原创直筒版型，100%纯棉，经典五袋款，永不过时", 599.00),
            ("Levi's 511修身牛仔裤", "修身版型，弹力面料，舒适贴身，商务休闲", 699.00),
            ("Uniqlo摇粒绒外套", "保暖透气，轻便舒适，多色可选，秋冬必备", 199.00),
            ("Champion卫衣", "经典刺绣Logo，纯棉面料，oversize版型，美式复古", 399.00),
            ("Nike Dri-FIT运动T恤", "速干排汗，透气舒适，运动训练必备", 199.00),
            ("Adidas三叶草卫衣", "经典Logo，纯棉面料，连帽设计，街头潮流", 499.00),
            ("MUJI无印良品衬衫", "纯棉免烫，简约设计，商务休闲皆宜", 299.00),
            ("海澜之家西装外套", "商务正装，修身版型，羊毛面料，职场必备", 899.00),
            ("GXG男装夹克", "时尚休闲，修身版型，多场合适用", 699.00),
            ("太平鸟男装毛衣", "羊毛混纺，保暖舒适，简约百搭", 399.00),
            ("森马羽绒服", "80%白鸭绒，轻薄保暖，性价比之选", 399.00),
            ("美特斯邦威卫衣", "纯棉加厚，舒适保暖，国民品牌", 199.00),
            ("班尼路T恤", "纯棉面料，多色可选，基础款百搭", 79.00),
            ("以纯牛仔裤", "弹力面料，修身版型，青春潮流", 199.00),
            ("真维斯休闲裤", "纯棉面料，舒适透气，休闲百搭", 159.00),
            
            # 箱包 (15个)
            ("新秀丽拉杆箱20寸", "PC材质，万向轮，TSA海关锁，轻便耐用", 699.00),
            ("新秀丽拉杆箱28寸", "大容量，静音万向轮，防刮耐磨，商务出行", 999.00),
            ("Rimowa Original拉杆箱", "铝镁合金，经典凹槽设计，德国制造，奢华旅行", 6999.00),
            ("小米旅行箱20寸", "PC+ABS材质，TSA锁，静音万向轮，性价比高", 299.00),
            ("90分拉杆箱", "德国拜耳PC材质，静音万向轮，简约设计", 399.00),
            ("Nike双肩包", "大容量，多隔层，透气背负，运动休闲", 299.00),
            ("Adidas运动背包", "防水面料，独立鞋仓，健身训练必备", 259.00),
            ("小米都市背包", "商务简约，15.6寸电脑仓，防泼水面料", 149.00),
            ("北面双肩包", "户外背包，大容量，防水耐磨，徒步旅行", 699.00),
            ("Herschel双肩包", "加拿大品牌，简约复古，多色可选，学生首选", 599.00),
            ("Longchamp饺子包", "法国轻奢，尼龙面料，轻便实用，女性必备", 999.00),
            ("Coach蔻驰托特包", "真皮材质，美式轻奢，通勤包包", 2999.00),
            ("Michael Kors手提包", "经典款式，PVC材质，轻奢品牌", 1899.00),
            ("Fossil化石邮差包", "复古设计，真皮材质，商务休闲", 1299.00),
            ("Kipling凯浦林斜挎包", "尼龙面料，轻便防水，猩猩挂饰", 599.00),
        ]
        
        for name, desc, price in fashion_items:
            products.append(Product(
                name=name,
                description=desc,
                price=price,
                stock=random.randint(20, 200),
                category_id=category_ids.get('fashion'),
                vendor_id=vendor_id,
                is_active=True,
                image_url="https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"
            ))
        
        # ==================== 家居用品 (40个) ====================
        home_items = [
            ("小米空气净化器4 Pro", "CADR值600m³/h，除甲醛除PM2.5，智能互联，适用60㎡", 1699.00),
            ("戴森V15 Detect无线吸尘器", "激光探测，230AW吸力，LCD屏幕，整屋深度清洁", 4990.00),
            ("石头扫地机器人T8 Pro", "激光导航，2700Pa吸力，拖扫一体，智能规划路径", 2999.00),
            ("科沃斯T20 Pro扫地机器人", "dToF导航，6000Pa吸力，热水净洗，全自动清洁", 3999.00),
            ("美的空调1.5匹变频", "一级能效，静音运行，智能温控，节能省电", 2399.00),
            ("格力空调大1匹变频", "新一级能效，自清洁，智能语音，品质保证", 2199.00),
            ("海尔冰箱三门风冷无霜", "风冷无霜，干湿分储，一级能效，家庭必备", 2999.00),
            ("西门子冰箱对开门", "零度保鲜，风冷无霜，大容量，德国品质", 6999.00),
            ("小米电视65寸4K", "4K超高清，HDR10+，120Hz刷新率，智能语音", 2999.00),
            ("索尼X95K 65寸电视", "XR认知芯片，4K 120Hz，HDMI2.1，游戏电视旗舰", 9999.00),
            ("海信激光电视100寸", "激光光源，4K分辨率，超短焦投影，护眼观影", 19999.00),
            ("北鼎养生壶", "厚玻璃壶身，多功能烹饪，精准控温，养生必备", 299.00),
            ("九阳破壁机", "2200W大功率，降噪设计，多功能料理，营养保留", 799.00),
            ("美的电压力锅", "一键烹饪，24小时预约，多重安全保护，省时省力", 399.00),
            ("苏泊尔电饭煲", "IH电磁加热，柴火饭程序，智能预约，煮饭神器", 599.00),
            ("宜家马尔姆床架", "现代简约，实木框架，坚固耐用，性价比高", 1299.00),
            ("慕思床垫乳胶独立弹簧", "独立袋装弹簧，天然乳胶，护脊睡眠，健康舒适", 5999.00),
            ("顾家家居真皮沙发", "头层牛皮，实木框架，现代简约，客厅首选", 8999.00),
            ("林氏木业北欧沙发", "布艺沙发，羽绒填充，可拆洗，舒适柔软", 3999.00),
            ("全友家居餐桌椅组合", "实木餐桌，可伸缩设计，4-6人适用，家庭聚餐", 2299.00),
            ("宜家汉尼斯办公椅", "人体工学，可调高度，透气网背，久坐舒适", 499.00),
            ("西昊人体工学椅", "铝合金底盘，3D扶手，透气网布，办公电竞", 1299.00),
            ("网易严选四件套", "60支长绒棉，A类亲肤，柔软舒适，多色可选", 399.00),
            ("水星家纺蚕丝被", "100%桑蚕丝，轻盈保暖，柔软亲肤，冬季必备", 1299.00),
            ("罗莱家纺羽绒被", "95%白鹅绒，充绒量2000g，蓬松保暖，品质之选", 2999.00),
            ("富安娜枕头", "记忆棉枕芯，护颈设计，舒适透气，改善睡眠", 299.00),
            ("飞利浦智能灯泡", "1600万色调光，语音控制，APP控制，智能家居", 99.00),
            ("欧普LED吸顶灯", "超薄设计，节能护眼，遥控调光，客厅卧室适用", 399.00),
            ("Yeelight智能台灯", "无线充电，触控调光，护眼模式，学习办公", 299.00),
            ("松下浴霸风暖", "快速制暖，超薄设计，低噪音，浴室专用", 699.00),
            ("科勒花洒套装", "304不锈钢，增压设计，三档出水，舒适沐浴", 899.00),
            ("九牧智能马桶", "即热式，自动翻盖，暖风烘干，抗菌喷头", 3999.00),
            ("老板油烟机侧吸", "22m³/min大吸力，自动清洗，低噪音，厨房必备", 2999.00),
            ("方太燃气灶", "4.5kW大火力，熄火保护，易清洁，安全可靠", 1999.00),
            ("美的洗碗机嵌入式", "13套容量，72℃高温除菌，烘干存储，解放双手", 3999.00),
            ("小天鹅洗衣机滚筒", "10kg容量，变频电机，95℃高温筒自洁，静音洗涤", 2599.00),
            ("海尔洗衣机波轮", "8kg容量，智能预约，多种洗涤模式，经济实用", 1299.00),
            ("追觅洗地机", "吸拖洗烘一体，智能清洁，60分钟续航，地面清洁神器", 2299.00),
            ("添可洗地机", "智能污水分离，电解水除菌，语音提示，高端清洁", 3999.00),
            ("小米电暖器", "快速制暖，IPX4防水，智能恒温，冬季取暖", 399.00),
        ]
        
        for name, desc, price in home_items:
            products.append(Product(
                name=name,
                description=desc,
                price=price,
                stock=random.randint(10, 100),
                category_id=category_ids.get('home'),
                vendor_id=vendor_id,
                is_active=True,
                image_url="https://images.unsplash.com/photo-1555041469-a586c61ea9bc?w=400"
            ))
        
        # ==================== 图书音像 (30个) ====================
        books = [
            ("Vue.js设计与实现", "霍春阳著，深入理解Vue3响应式原理，掌握框架设计精髓，前端进阶必读", 89.00),
            ("JavaScript高级程序设计（第4版）", "红宝书，全面讲解JavaScript核心技术，Web开发经典教材", 109.00),
            ("深入理解计算机系统（第3版）", "CSAPP经典教材，从程序员角度学习计算机系统，CS专业必读", 139.00),
            ("算法导论（第3版）", "MIT经典教材，算法领域的圣经，全面深入讲解算法设计与分析", 128.00),
            ("Python编程：从入门到实践（第3版）", "零基础入门Python，包含大量实例和项目，适合初学者", 99.00),
            ("流畅的Python（第2版）", "Python进阶必读，深入理解Python特性，提升编程能力", 139.00),
            ("代码整洁之道", "Robert C. Martin著，如何编写可读性强的代码，程序员必修课", 89.00),
            ("重构：改善既有代码的设计（第2版）", "Martin Fowler经典之作，提升代码质量的实用指南", 128.00),
            ("设计模式：可复用面向对象软件的基础", "GoF经典，23种设计模式详解，软件工程必读", 79.00),
            ("深入理解Java虚拟机（第3版）", "周志明著，JVM底层原理深度剖析，Java开发进阶", 119.00),
            ("Effective Java（第3版）", "Joshua Bloch著，Java编程最佳实践，Java开发者必读", 99.00),
            ("Head First设计模式", "图文并茂，生动有趣，设计模式入门首选", 98.00),
            ("MySQL必知必会", "MySQL入门经典，快速掌握数据库基础知识", 49.00),
            ("Redis设计与实现", "黄健宏著，深入Redis内部机制，掌握缓存技术", 89.00),
            ("Kubernetes权威指南（第5版）", "K8s经典教材，云原生技术实战指南", 158.00),
            ("Docker技术入门与实战（第3版）", "容器技术入门，从基础到实战，DevOps必备", 89.00),
            ("人月神话", "软件工程经典，项目管理必读，程序员的智慧结晶", 55.00),
            ("黑客与画家", "Paul Graham著，探讨黑客精神与创业思考", 49.00),
            ("三体（全集）", "刘慈欣著，科幻巨作，雨果奖获奖作品，中国科幻里程碑", 89.00),
            ("百年孤独", "加西亚·马尔克斯著，魔幻现实主义巨作，诺贝尔文学奖", 45.00),
            ("活着", "余华著，当代文学经典，生命的韧性与尊严", 25.00),
            ("平凡的世界（全三册）", "路遥著，茅盾文学奖获奖作品，励志经典", 99.00),
            ("红楼梦", "曹雪芹著，中国古典文学四大名著之首", 68.00),
            ("人类简史", "尤瓦尔·赫拉利著，从动物到上帝，人类发展史", 68.00),
            ("未来简史", "尤瓦尔·赫拉利著，探讨人类未来的发展方向", 68.00),
            ("原则", "瑞·达利欧著，生活和工作的原则，个人成长必读", 98.00),
            ("高效能人士的七个习惯", "史蒂芬·柯维著，自我提升经典，改变思维方式", 59.00),
            ("穷爸爸富爸爸", "罗伯特·清崎著，财商教育入门，理财启蒙书", 42.00),
            ("小王子", "圣埃克苏佩里著，永恒的童话，关于爱与责任", 35.00),
            ("围城", "钱钟书著，中国现代文学经典，讽刺喜剧杰作", 39.00),
        ]
        
        for name, desc, price in books:
            products.append(Product(
                name=name,
                description=desc,
                price=price,
                stock=random.randint(50, 300),
                category_id=category_ids.get('books'),
                vendor_id=vendor_id,
                is_active=True,
                image_url="https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=400"
            ))
        
        print(f"\n开始添加 {len(products)} 个商品...")
        print("=" * 80)
        
        electronics_count = 0
        fashion_count = 0
        home_count = 0
        books_count = 0
        
        for i, product in enumerate(products, 1):
            db.add(product)
            # 统计分类
            if product.category_id == category_ids.get('electronics'):
                electronics_count += 1
            elif product.category_id == category_ids.get('fashion'):
                fashion_count += 1
            elif product.category_id == category_ids.get('home'):
                home_count += 1
            elif product.category_id == category_ids.get('books'):
                books_count += 1
            
            if i % 20 == 0:
                print(f"  进度: [{i}/{len(products)}] 已添加 {i} 个商品...")
        
        await db.commit()
        print(f"\n[成功] 成功添加 {len(products)} 个商品！")
        print("\n[统计] 商品统计:")
        print("=" * 80)
        print(f"  [电子产品] {electronics_count} 个")
        print(f"     - 手机：30个（包含iPhone、华为、小米、OPPO、vivo、三星、荣耀等品牌）")
        print(f"     - 笔记本：15个（包含MacBook、华为、联想、戴尔等品牌）")
        print(f"     - 其他：15个（平板、耳机、手表、相机等）")
        print(f"  [服装鞋包] {fashion_count} 个")
        print(f"     - 运动鞋：15个")
        print(f"     - 服装：20个")
        print(f"     - 箱包：15个")
        print(f"  [家居用品] {home_count} 个")
        print(f"  [图书音像] {books_count} 个")
        print("\n[重点] 重点商品:")
        print("  [OPPO手机系列]")
        print("     - OPPO Find X7 Ultra (5999元)")
        print("     - OPPO Find X7 Pro (4999元)")
        print("     - OPPO Find X7 (3999元)")
        print("     - OPPO Find N3 折叠屏 (8999元)")
        print("     - OPPO Reno11 Pro (3299元)")
        print("     - OPPO Reno11 (2699元)")
        print("     - OPPO K12 性价比之选 (1999元)")
        print("     - OPPO A2 Pro (1699元)")
        print("\n[下一步] 现在可以重建向量数据库了！")
        print("   运行命令: python init_knowledge_base.py --rebuild")
        print("   前端地址: http://localhost:3000/products")


if __name__ == "__main__":
    print("="*60)
    print("          快速添加示例商品数据")
    print("="*60)
    asyncio.run(add_sample_products())

