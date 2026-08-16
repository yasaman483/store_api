from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import func
from schemas.products import ProductsCreate, ProductsUpdateGet, ProductsUpdateSent, GetProductId, GetProductName
from models.products import Products
from models.people import People
from models.categories import Categories
from schemas.people import Roles


async def create_product(product: ProductsCreate, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')

    try:
        result = await db.execute(select(Categories).where(func.lower(
            Categories.category_name) == product.category_name.lower()))

        product_category = result.scalar_one_or_none()

        if product_category is None:
            raise HTTPException(status_code=404, detail='Category not found')

        new_product = Products(
            product_name=product.product_name,
            unit_price=product.unit_price,
            remain_in_stock=product.remain_in_stock,
            category_id=product_category.category_id
        )

        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)
        return new_product

    except Exception as ex:
        await db.rollback()
        raise ex


async def get_all_products(db: AsyncSession):
    result = await db.execute(select(Products))

    products = result.scalars().all()

    if not products:
        raise HTTPException(status_code=404, detail='No products added yet')

    return products


async def get_product_by_name(product: GetProductName, db: AsyncSession):
    result = await db.execute(select(Products).where(
        Products.product_name == product.product_name))

    searched_product = result.scalar_one_or_none()

    if searched_product is None:
        raise HTTPException(
            status_code=404, detail=f'Product {product.product_name} not found')

    return searched_product


async def get_product_by_id(product: GetProductId, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(Products).where(
        Products.product_id == product.product_id))

    searched_product = result.scalar_one_or_none()

    if searched_product is None:
        raise HTTPException(
            status_code=404, detail=f'Product {product.product_id} not found')

    return searched_product


async def update_product(current_product: ProductsUpdateSent, updated_product: ProductsUpdateGet, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')
    try:
        result = await db.execute(select(Products).where(
            Products.product_name == current_product.product_name))

        product = result.scalar_one_or_none()

        if product is None:
            raise HTTPException(
                status_code=404, detail=f'Product {current_product.product_name} not found')

        update_data = updated_product.model_dump(exclude_unset=True)

        if "category_name" in update_data.keys():
            result = await db.execute(select(Categories).where(
                Categories.category_name == updated_product.category_name))

            category = result.scalar_one_or_none()

            update_data["category_id"] = category.category_id

        for key, value in update_data.items():
            setattr(product, key, value)

        await db.commit()
        await db.refresh(product)
        return product

    except Exception as ex:
        await db.rollback()
        raise ex


async def delete_product(product: ProductsUpdateSent, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')

    try:
        result = await db.execute(select(Products).where(
            Products.product_name == product.product_name))

        searched_product = result.scalar_one_or_none()

        if searched_product is None:
            raise HTTPException(
                status_code=404, detail=f'Product {product.product_name} not found')

        await db.delete(searched_product)
        await db.commit()

        return {"message": f"Product {product.product_name} deleted successfully."}

    except Exception as ex:
        await db.rollback()
        raise ex
