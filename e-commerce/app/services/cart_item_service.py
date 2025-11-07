from sqlalchemy.future import select
from fastapi  import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product
from app.models.cart_item import CartItem
from app.schemas.cart_item import CartItemCreate, CartItemResponse


class CartService:
  @staticmethod
  async def create_cart_item(
          cart_item_data: CartItemCreate,
          db: AsyncSession, current_user):

    # 1. 检查商品是否存在且有效
    product_query = select(Product).where(Product.id == cart_item_data.product_id)
    product_result = await db.execute(product_query)
    product_item = product_result.scalars().first()

    if not product_item or product_item.is_active == False:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                          detail='Product not found')

    # 2. 检查购物车中是否已存在该商品
    existing_cart_item_query = select(CartItem).where(
        CartItem.user_id == current_user.id,
        CartItem.product_id == cart_item_data.product_id
    )
    existing_cart_item_result = await db.execute(existing_cart_item_query)
    existing_cart_item = existing_cart_item_result.scalars().first()

    if existing_cart_item:
      # 如果已存在，累加数量
      new_quantity = existing_cart_item.quantity + cart_item_data.quantity
      
      # 检查库存是否足够
      if product_item.stock < new_quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Product stock exceeded. Available stock: {product_item.stock}, current in cart: {existing_cart_item.quantity}')
      
      # 更新数量和价格
      existing_cart_item.quantity = new_quantity
      existing_cart_item.price = product_item.price * new_quantity
      
      await db.commit()
      await db.refresh(existing_cart_item)
      return CartItemResponse.model_validate(existing_cart_item)
    
    else:
      # 如果不存在，创建新记录
      if product_item.stock < cart_item_data.quantity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f'Product stock exceeded. Available stock: {product_item.stock}')

      cart_item_dict = cart_item_data.model_dump()
      cart_item_dict['user_id'] = current_user.id
      cart_item_dict['price'] = product_item.price * cart_item_data.quantity
      
      cart_item = CartItem(**cart_item_dict)
      db.add(cart_item)
      await db.commit()
      await db.refresh(cart_item)
      return CartItemResponse.model_validate(cart_item)

  @staticmethod
  async def get_cart_items(db: AsyncSession, current_user):
    cart_query = select(CartItem).where(CartItem.user_id == current_user.id)
    cart_items_result = await db.execute(cart_query)
    cart_items = cart_items_result.scalars().all()

    # 转换为Pydantic模型以确保所有字段都被正确序列化
    return [CartItemResponse.model_validate(item) for item in cart_items]

  @staticmethod
  async def get_cart_item_by_id(cart_item_id: int, db: AsyncSession, current_user):
    cart_item_query = select(CartItem).where(CartItem.id == cart_item_id)
    cart_item_result = await db.execute(cart_item_query)
    cart_item = cart_item_result.scalar_one_or_none()

    if not cart_item:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Cart Item not found')

    if not cart_item.user_id == current_user.id:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    return CartItemResponse.model_validate(cart_item)

  @staticmethod
  async def update_cart_item(cart_item_id: int, cart_item, db: AsyncSession, current_user):
    # 查询购物车项（用于权限验证）
    cart_item_query = select(CartItem).where(CartItem.id == cart_item_id)
    cart_item_db_result = await db.execute(cart_item_query)
    cart_item_db = cart_item_db_result.scalar_one_or_none()
    
    if not cart_item_db:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Cart Item not found')
    
    if cart_item_db.user_id != current_user.id:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    # 检查商品库存
    product_result = await db.execute(select(Product).where(Product.id == cart_item_db.product_id))
    product = product_result.scalar_one_or_none()
    if cart_item.quantity > product.stock:
      raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                          detail=f"Product stock exceeded. Available stock: {product.stock}")
    
    # 更新数量和价格
    cart_item_db.quantity = cart_item.quantity
    cart_item_db.price = product.price * cart_item_db.quantity

    db.add(cart_item_db)
    await db.commit()
    await db.refresh(cart_item_db)
    
    return CartItemResponse.model_validate(cart_item_db)

  @staticmethod
  async def delete_cart_item(cart_item_id: int, db: AsyncSession, current_user):
    cart_item_query = select(CartItem).where(CartItem.id == cart_item_id)
    cart_item_result = await db.execute(cart_item_query)
    cart_item = cart_item_result.scalar_one_or_none()

    if not cart_item:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Cart Item not found')

    if not cart_item.user_id == current_user.id:
      raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    await db.delete(cart_item)
    await db.commit()
    return {"message": "Cart item deleted successfully"}