from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from sqlalchemy import func
from schemas.products import ProductCreate, ProductUpdateGet, GetProductId, ProductStatus, FilterProduct, GetProduct
from models.products import Product
from models.people import Person
from models.categories import Category
from schemas.categories import CategoryCondition
from schemas.people import Roles
from schemas.wallet import SortOrder
from crud.wallet import make_json_format
import logging
from schemas.audit import AuditContext, AuditStatus
from crud.audit_log import create_audit_log
from math import ceil

logger = logging.getLogger(__name__)


async def create_product(product: ProductCreate, audit: AuditContext, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="product",
            event="PRODUCT_CREATED",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail='Not authorized for creating product.')

    try:
        result = await db.execute(select(Category).where(func.lower(
            Category.category_name) == product.category_name.lower()))

        product_category = result.scalar_one_or_none()

        if product_category is None:
            raise HTTPException(
                status_code=404, detail=f'Category {product.category_name} not found')

        if product_category.category_situation == CategoryCondition.UNACTIVE:
            raise HTTPException(
                status_code=403, detail="The category is unactivated")

        new_product = Product(
            product_name=product.product_name.lower(),
            unit_price=product.unit_price,
            remain_in_stock=product.remain_in_stock,
            category_id=product_category.category_id,
            product_status=product.product_status
        )

        db.add(new_product)
        await db.flush()

        new_value = {column.key: getattr(
            new_product, column.key) for column in inspect(Product).mapper.column_attrs}

        new_value = make_json_format(new_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=new_product.product_id,
            entity_type="product",
            event="PRODUCT_CREATED",
            old_value=None,
            new_value=new_value
        )

        await db.commit()
        await db.refresh(new_product)

        return new_product

    except HTTPException:
        await db.rollback()
        raise

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="confliction happend")

    except Exception:
        logger.exception(f"Create product {product.product_name} failed")
        await db.rollback()
        raise


async def get_all_products(filter_product: FilterProduct, db: AsyncSession):
    filters = []
    if filter_product.product_id is not None:
        filters.append(Product.product_id == filter_product.product_id)
    if filter_product.product_name is not None:
        filters.append(Product.product_name == filter_product.product_name)
    if filter_product.min_unit_price is not None:
        filters.append(Product.unit_price >= filter_product.min_unit_price)
    if filter_product.max_unit_price is not None:
        filters.append(Product.unit_price <= filter_product.max_unit_price)
    if filter_product.min_remain_in_stock is not None:
        filters.append(Product.remain_in_stock >=
                       filter_product.min_remain_in_stock)
    if filter_product.max_remain_in_stock is not None:
        filters.append(Product.remain_in_stock <=
                       filter_product.max_remain_in_stock)
    if filter_product.category_name is not None:
        result = await db.execute(select(Category).where(Category.category_name == filter_product.category_name))
        category = result.scalar_one_or_none()

        if category is None:
            raise HTTPException(status_code=404, detail="Category not found")

        filters.append(Product.category_id == category.category_id)

    if filter_product.product_status:
        filters.append(Product.product_status == filter_product.product_status)

    query = select(Product).where(*filters)
    result = select(func.count()).select_from(query.subquery())
    total = await db.scalar(result)
    offset = (filter_product.page - 1)*filter_product.page_size

    if filter_product.sort_order == SortOrder.ASC:
        query = query.order_by(asc(filter_product.sort_by)).offset(
            offset).limit(filter_product.page_size)

    if filter_product.sort_order == SortOrder.DES:
        query = query.order_by(desc(filter_product.sort_by)).offset(
            offset).limit(filter_product.page_size)

    result = await db.execute(query)

    products = result.scalars().all()

    if not products:
        raise HTTPException(status_code=404, detail='No products added yet')

    return GetProduct(products=products, page=filter_product.page, page_size=filter_product.page_size, total=total, pages=ceil(total/filter_product.page_size))


async def update_product(current_product: GetProductId, updated_product: ProductUpdateGet, audit: AuditContext, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=current_product.product_id,
            entity_type="product",
            event="PRODUCT_UPDATED",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail='Not authorized for updating product')

    try:
        result = await db.execute(select(Product).where(
            Product.product_id == current_product.product_id))

        product = result.scalar_one_or_none()

        if product is None:
            raise HTTPException(
                status_code=404, detail=f'Product {current_product.product_id} not found')

        if product.product_status == ProductStatus.UNACTIVE and updated_product.product_status and updated_product.product_status != ProductStatus.ACTIVE:
            raise HTTPException(
                status_code=403, detail="The product is unacativated")

        update_data = updated_product.model_dump(exclude_unset=True)

        if "category_name" in update_data.keys():
            result = await db.execute(select(Category).where(
                func.lower(Category.category_name) == updated_product.category_name.lower()))

            category = result.scalar_one_or_none()

            if category is None:
                raise HTTPException(
                    status_code=404, detail=f"Category {updated_product.category_name} not found")

            if category.category_situation == CategoryCondition.UNACTIVE:
                raise HTTPException(
                    status_code=403, detail="The category is unactived")

            update_data["category_id"] = category.category_id
            update_data.pop("category_name")

        if "product_name" in update_data.keys():
            update_data["product_name"] = update_data["product_name"].lower()

        old_value = dict()
        new_value = dict()
        for key, value in update_data.items():
            old_value[key] = getattr(product, key)
            new_value[key] = value
            setattr(product, key, value)

        old_value = make_json_format(old_value)
        new_value = make_json_format(new_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=current_product.product_id,
            entity_type="product",
            event="PRODUCT_UPDATED",
            old_value=old_value,
            new_value=new_value
        )

        await db.commit()
        await db.refresh(product)

        return product

    except HTTPException:
        await db.rollback()
        raise

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Confliction happend")

    except Exception:
        logger.exception(f"Update product {current_product.product_id} failed")

        await db.rollback()
        raise


async def unactive_product(product: GetProductId, audit: AuditContext, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=product.product_id,
            entity_type="product",
            event="PRODUCT_UNACTIVATED",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail='Not authorized for deleting product')

    try:
        result = await db.execute(select(Product).where(
            Product.product_id == product.product_id))

        searched_product = result.scalar_one_or_none()

        if searched_product is None:
            raise HTTPException(
                status_code=404, detail=f'Product {product.product_id} not found')

        old_value = {column.key: getattr(
            searched_product, column.key) for column in inspect(Product).mapper.column_attrs}

        searched_product.product_status = ProductStatus.UNACTIVE

        new_value = {column.key: getattr(
            searched_product, column.key) for column in inspect(Product).mapper.column_attrs}

        new_value = make_json_format(new_value)
        old_value = make_json_format(old_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=product.product_id,
            entity_type="product",
            event="PRODUCT_UNACTIVATED",
            old_value=old_value,
            new_value=new_value
        )
        await db.commit()

        return {"message": f"Product {product.product_id} unactivated successfully."}

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        logger.exception(f"Unactivate product {product.product_id} failed")

        await db.rollback()
        raise
