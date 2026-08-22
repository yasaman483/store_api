from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import func
from schemas.products import ProductCreate, ProductUpdateGet, GetProductId, GetProductName
from models.products import Product
from models.people import Person
from models.categories import Category
from schemas.people import Roles
import logging
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


async def create_product(product: ProductCreate, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        error = {
            "event": "Create product failed",
            "method": "POST",
            "error": "Not authorized to create product.",
            "path": "/products/add_product",
            "user_id": current_user.user_id,
            "status_code": 403
        }
        logger.error(error)
        raise HTTPException(
            status_code=403, detail='Not authorized for creating product.')

    try:
        result = await db.execute(select(Category).where(func.lower(
            Category.category_name) == product.category_name.lower()))

        product_category = result.scalar_one_or_none()

        if product_category is None:
            raise HTTPException(status_code=404, detail='Category not found')

        new_product = Product(
            product_name=product.product_name,
            unit_price=product.unit_price,
            remain_in_stock=product.remain_in_stock,
            category_id=product_category.category_id
        )

        db.add(new_product)
        await db.commit()
        await db.refresh(new_product)

        end_time = datetime.now(UTC)
        info = {
            "event": "Create poduct succeeded",
            "method": "POST",
            "path": "/products/add_product",
            "user_id": current_user.user_id,
            "added_category": new_product.product_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return new_product

    except Exception as ex:
        end_time = datetime.now(UTC)
        error = {
            "event": "Create product failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/products/add_product",
            "user_id": current_user.user_id,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        await db.rollback()
        raise ex


async def get_all_products(current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    result = await db.execute(select(Product))

    products = result.scalars().all()

    if not products:
        raise HTTPException(status_code=404, detail='No products added yet')

    end_time = datetime.now(UTC)
    info = {
        "event": "Get all poducts succeeded",
        "method": "POST",
        "path": "/products/add_product",
        "user_id": current_user.user_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return products


async def get_product_by_name(product: GetProductName, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    result = await db.execute(select(Product).where(
        Product.product_name == product.product_name))

    searched_product = result.scalar_one_or_none()

    if searched_product is None:
        raise HTTPException(
            status_code=404, detail=f'Product {product.product_name} not found')

    end_time = datetime.now(UTC)
    info = {
        "event": "Get poduct by name succeeded",
        "method": "POST",
        "path": "/products/get_product_by_name",
        "user_id": current_user.user_id,
        "product_name": product.product_name,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return searched_product


async def get_product_by_id(product: GetProductId, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        error = {
            "event": "Get product by id failed",
            "method": "POST",
            "error": "Not authorized to get products by id",
            "path": "/products/get_product_by_id",
            "user_id": current_user.user_id,
            "status_code": 403
        }
        logger.error(error)

        raise HTTPException(
            status_code=403, detail="Not authorized for gettung product by id")

    result = await db.execute(select(Product).where(
        Product.product_id == product.product_id))

    searched_product = result.scalar_one_or_none()

    if searched_product is None:
        raise HTTPException(
            status_code=404, detail=f'Product {product.product_id} not found')

    end_time = datetime.now(UTC)
    info = {
        "event": "Get poduct by id succeeded",
        "method": "POST",
        "path": "/products/get_product_by_id",
        "user_id": current_user.user_id,
        "product_id": product.product_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return searched_product


async def update_product(current_product: GetProductId, updated_product: ProductUpdateGet, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        error = {
            "event": "Update product failed",
            "method": "POST",
            "error": "Not authorized to delete product",
            "path": "/products/delete_product",
            "user_id": current_user.user_id,
            "status_code": 403
        }
        logger.error(error)

        raise HTTPException(
            status_code=403, detail='Not authorized for deleting product')

    try:
        result = await db.execute(select(Product).where(
            Product.product_id == current_product.product_id))

        product = result.scalar_one_or_none()

        if product is None:
            raise HTTPException(
                status_code=404, detail=f'Product {current_product.product_id} not found')

        update_data = updated_product.model_dump(exclude_unset=True)

        if "category_name" in update_data.keys():
            result = await db.execute(select(Category).where(
                Category.category_name == updated_product.category_name))

            category = result.scalar_one_or_none()

            update_data["category_id"] = category.category_id

        for key, value in update_data.items():
            setattr(product, key, value)

        await db.commit()
        await db.refresh(product)

        end_time = datetime.now(UTC)
        info = {
            "event": "Update product succeeded",
            "method": "POST",
            "path": "/products/update_product",
            "user_id": current_user.user_id,
            "product_id": product.product_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return product

    except Exception as ex:
        end_time = datetime.now(UTC)
        error = {
            "event": "Update product failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/products/update_product",
            "user_id": current_user.user_id,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)

        await db.rollback()
        raise ex


async def delete_product(product: GetProductId, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        error = {
            "event": "Delete product failed",
            "method": "POST",
            "error": "Not authorized to delete product",
            "path": "/products/delete_product",
            "user_id": current_user.user_id,
            "status_code": 403
        }
        logger.error(error)

        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')

    try:
        result = await db.execute(select(Product).where(
            Product.product_id == product.product_id))

        searched_product = result.scalar_one_or_none()

        if searched_product is None:
            raise HTTPException(
                status_code=404, detail=f'Product {product.product_id} not found')

        end_time = datetime.now(UTC)
        info = {
            "event": "Delete product succeeded",
            "method": "POST",
            "path": "/products/update_product",
            "user_id": current_user.user_id,
            "product_id": product.product_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        await db.delete(searched_product)
        await db.commit()

        return {"message": f"Product {product.product_id} deleted successfully."}

    except Exception as ex:
        end_time = datetime.now(UTC)
        error = {
            "event": "Delete product failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/products/delete_product",
            "user_id": current_user.user_id,
            "product_id": product.product_id,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)

        await db.rollback()
        raise ex
