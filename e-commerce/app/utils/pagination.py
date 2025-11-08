from sqlalchemy import and_, func
from sqlalchemy.future import select
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wishlist import Wishlist
from app.schemas.product import ProductFilter
from app.schemas.wishlist import WishlistFilter
from app.models.product import Product

async def apply_filters(db: AsyncSession, filters: ProductFilter):
    # Validate price range
    if filters.min_price is not None and filters.max_price is not None:
        if filters.min_price > filters.max_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="min_price cannot be greater than max_price."
            )

    # Validate category_id (if provided, check if it's a positive integer)
    if filters.category is not None:
        try:
            category_id = int(filters.category)
            if category_id < 1:
                raise ValueError()
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid category: {filters.category}. Category must be a positive integer (category ID)."
            )

    # Build dynamic conditions
    conditions = []

    # availability can be True OR False → check None explicitly
    if filters.availability is not None:
        conditions.append(Product.is_active == filters.availability)

    if filters.category is not None:
        conditions.append(Product.category_id == int(filters.category))

    if filters.min_price is not None:
        conditions.append(Product.price >= filters.min_price)

    if filters.max_price is not None:
        conditions.append(Product.price <= filters.max_price)

    # Base query
    query = select(Product)
    if conditions:
        query = query.where(and_(*conditions))

    return query

async def apply_pagination(query, filters: ProductFilter, db: AsyncSession):
    # Validate params
    if filters.page < 1 or filters.size < 1 or filters.size > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid pagination parameters. Page must be >= 1 and size must be between 1 and 100."
        )

    # Get total count (without LIMIT/OFFSET)
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    # Apply pagination
    offset = (filters.page - 1) * filters.size
    paginated_query = query.offset(offset).limit(filters.size)
    result = await db.execute(paginated_query)
    items = result.scalars().all()

    # Return structured response
    return {
        "items": items,
        "total": total,
        "page": filters.page,
        "size": filters.size,
        "pages": (total + filters.size - 1) // filters.size  # total pages
    }

async def apply_wishlist_filters(filters: WishlistFilter, current_user):
  if (filters.min_price and filters.max_price) and (filters.min_price > filters.max_price):
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="min price cannot be greater than max price.")

  conditions = [Wishlist.user_id == current_user.id]

  if filters.availability:
    conditions.append(Product.is_active == filters.availability)

  if filters.category:
    try:
      category_id = int(filters.category)
      conditions.append(Product.category_id == category_id)
    except (ValueError, TypeError):
      raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Invalid category: {filters.category}. Category must be a category ID."
      )

  if filters.min_price:
    conditions.append(Product.price >= filters.min_price)

  if filters.max_price:
    conditions.append(Product.price <= filters.max_price)

  query = (select(Product)
           .join(Wishlist, Wishlist.product_id == Product.id)
           .where(and_(*conditions)))

  return query

async def apply_wishlist_pagination(query, filters: WishlistFilter, db: AsyncSession):
  if filters.page < 1 or filters.size < 1 or filters.size > 100:
    raise HTTPException(
      status_code=status.HTTP_400_BAD_REQUEST,
      detail="Invalid pagination parameters. Page must be >= 1 and size must be between 1 and 100.")

  offset = (filters.page - 1) * filters.size
  paginated_query = query.offset(offset).limit(filters.size)
  result = await db.execute(paginated_query)
  items = result.scalars().all()

  return items