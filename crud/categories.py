from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from schemas.categories import CategoryCreate, GetCategoryId, CategoryCondition, CategoryUpdate, GetCategoryInfo
from models.categories import Category
from models.people import Person
from schemas.people import Roles
import logging
from crud.audit_log import create_audit_log
from schemas.audit import AuditContext, AuditStatus
from schemas.categories import FilterCategory
from schemas.wallet import SortOrder
from math import ceil

logger = logging.getLogger(__name__)


async def create_category(category: CategoryCreate, audit: AuditContext, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="category",
            event="CATEGORY_CREATED",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()
        raise HTTPException(
            status_code=403, detail='Not authorized for creating category.')
    try:
        new_category = Category(
            category_name=category.category_name.lower(),
            category_situation=category.category_situation if category.category_situation else CategoryCondition.ACTIVE
        )

        db.add(new_category)
        await db.flush()

        new_value = {column.key: getattr(
            new_category, column.key) for column in inspect(Category).mapper.column_attrs}

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=new_category.category_id,
            entity_type="category",
            event="CATEGORY_CREATED",
            old_value=None,
            new_value=new_value
        )
        await db.commit()
        await db.refresh(new_category)

        return new_category

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Confliction happend")

    except Exception:
        logger.exception(
            f"Create category failed for category {category.category_name}")
        await db.rollback()
        raise


async def get_all_categories(audit: AuditContext, filter_category: FilterCategory, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="category",
            event="CATEGORIES_READ",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail='Not authorized for getting all categories.')

    filters = []
    if filter_category.category_id is not None:
        filters.append(Category.category_id == filter_category.category_id)
    if filter_category.category_name is not None:
        filters.append(Category.category_name == filter_category.category_name)
    if filter_category.category_situation is not None:
        filters.append(filter_category.category_situation ==
                       Category.category_situation)

    query = select(Category).where(*filters)
    result = select(func.count()).select_from(query.subquery())
    total = await db.scalar(result)
    offset = (filter_category.page - 1)*filter_category.page_size

    if filter_category.sort_order == SortOrder.ASC:
        query = query.order_by(asc(filter_category.sort_by)).offset(
            offset).limit(filter_category.page_size)

    if filter_category.sort_order == SortOrder.DES:
        query = query.order_by(desc(filter_category.sort_by)).offset(
            offset).limit(filter_category.page_size)

    result = await db.execute(query)

    categories = result.scalars().all()

    if not categories:
        raise HTTPException(status_code=404, detail='No categories added yet')

    return GetCategoryInfo(categories=categories, page=filter_category.page, page_size=filter_category.page_size, total=total, pages=ceil(total/filter_category.page_size))


async def update_category(current_category: GetCategoryId, category: CategoryUpdate, audit: AuditContext, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=current_category.category_id,
            entity_type="category",
            event="CATEGORY_UPDATED",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail='Not authorized for updating category.')
    try:
        old_value = dict()
        new_value = dict()
        result = await db.execute(select(Category).where(
            Category.category_id == current_category.category_id))

        searched_category = result.scalar_one_or_none()

        if searched_category is None:
            raise HTTPException(
                status_code=404, detail=f'Category {current_category.category_id} not found.')

        if searched_category.category_situation == CategoryCondition.UNACTIVE and category.category_situation and category.category_situation != CategoryCondition.ACTIVE:
            raise HTTPException(
                status_code=403, detail="The category is unactivated")

        update_data = category.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            old_value[key] = value
            if key == "category_name":
                value = value.lower()
            setattr(searched_category, key, value)
            new_value[key] = value

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=current_category.category_id,
            entity_type="category",
            event="Update category",
            old_value=old_value,
            new_value=new_value
        )

        await db.commit()
        await db.refresh(searched_category)

        return searched_category

    except HTTPException:
        await db.rollback()
        raise

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Confliction happend")

    except Exception:
        logger.exception(
            f"Update category for category {current_category.category_id} failed")

        await db.rollback()
        raise


async def unactive_category(category: GetCategoryId, audit: AuditContext, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=category.category_id,
            entity_type="category",
            event="CATEGORY_UNACTIVATED",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail='Not authorized for deleting category.')
    try:
        result = await db.execute(select(Category).where(
            Category.category_id == category.category_id))

        searched_category = result.scalar_one_or_none()

        if searched_category is None:
            raise HTTPException(
                status_code=404, detail=f'Category {category.category_id} not found.')

        old_value = {column.key: getattr(
            searched_category, column.key) for column in inspect(Category).mapper.column_attrs}

        searched_category.category_situation = CategoryCondition.UNACTIVE
        await db.flush()

        new_value = {column.key: getattr(
            searched_category, column.key) for column in inspect(Category).mapper.column_attrs}

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=category.category_id,
            entity_type="category",
            event="CATEGORY_UNACTIVATED",
            old_value=old_value,
            new_value=new_value
        )
        await db.commit()

        return {"message": f"Category {category.category_id} unactivated successfully."}

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        logger.exception(
            f"Unactivation for category {category.category_id} failed",)

        await db.rollback()
        raise
