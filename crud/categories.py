from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schemas.categories import CategoryBase, CategoryCreate, GetCategoryId
from models.categories import Category
from models.people import Person
from schemas.people import Roles
import logging
from datetime import datetime, UTC

logger = logging.getLogger(__name__)


async def create_category(category: CategoryCreate, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        error = {
            "event": "Create category failed",
            "method": "POST",
            "error": "Not authorized to create category.",
            "path": "/categories/add_category",
            "user_id": current_user.user_id,
            "status_code": 403
        }
        logger.error(error)

        raise HTTPException(
            status_code=403, detail='Not authorized for creating category.')
    try:
        new_category = Category(
            category_name=category.category_name
        )

        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)

        end_time = datetime.now(UTC)
        info = {
            "event": "Create category succeeded",
            "method": "POST",
            "path": "/categories/add_category",
            "user_id": current_user.user_id,
            "added_category": new_category.category_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)
        return new_category

    except Exception as ex:
        error = {
            "event": "Create category failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/categories/add_category",
            "user_id": current_user.user_id
        }
        logger.error(error)
        await db.rollback()
        raise ex


async def get_all_categories(current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        error = {
            "event": "Get all categories failed",
            "method": "POST",
            "error": "Not authorized to get all categories.",
            "path": "/categories/get_categories",
            "user_id": current_user.user_id,
            "status_code": 403
        }
        logger.error(error)

        raise HTTPException(
            status_code=403, detail='Not authorized for getting all categories.')

    result = await db.execute(select(Category))

    categories = result.scalars().all()

    if categories is None:
        raise HTTPException(status_code=404, detail='No categories added yet')

    end_time = datetime.now(UTC)
    info = {
        "event": "Get all categories succeeded",
        "method": "POST",
        "path": "/categories/get_categories",
        "user_id": current_user.user_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return categories


async def get_category_by_id(category: GetCategoryId, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        error = {
            "event": "Get category by id failed",
            "method": "POST",
            "error": "Not authorized to get category by id",
            "path": "/categories/get_category",
            "user_id": current_user.user_id,
            "category_id": category.category_id,
            "status_code": 403
        }
        logger.error(error)

        raise HTTPException(
            status_code=403, detail='Not authorized for getting category.')

    result = await db.execute(select(Category).where(
        Category.category_id == category.category_id))

    searched_category = result.scalar_one_or_none()

    if searched_category is None:
        raise HTTPException(
            status_code=404, detail=f'category {category.category_id} not found')

    end_time = datetime.now(UTC)
    info = {
        "event": "Get category by id succeeded",
        "method": "POST",
        "path": "/categories/get_category",
        "user_id": current_user.user_id,
        "category_id": category.category_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return searched_category


async def update_category(current_category: GetCategoryId, category: CategoryCreate, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER:
        error = {
            "event": "Update category by id failed",
            "method": "POST",
            "error": "Not authorized to get category by id",
            "path": "/categories/update_category",
            "user_id": current_user.user_id,
            "category_id": current_category.category_id,
            "status_code": 403
        }
        logger.error(error)

        raise HTTPException(
            status_code=403, detail='Not authorized for getting category.')
    try:
        result = await db.execute(select(Category).where(
            Category.category_id == current_category.category_id))

        searched_category = result.scalar_one_or_none()

        if searched_category is None:
            raise HTTPException(
                status_code=404, detail=f'Category {current_category.category_id} not found.')

        searched_category.category_name = category.category_name

        await db.commit()
        await db.refresh(searched_category)

        end_time = datetime.now(UTC)
        info = {
            "event": "Update category by id succeeded",
            "method": "POST",
            "path": "/categories/update_category",
            "user_id": current_user.user_id,
            "category_id": current_category.category_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return searched_category

    except Exception as ex:
        end_time = datetime.now(UTC)
        error = {
            "event": "Update category by id failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/categories/update_category",
            "user_id": current_user.user_id,
            "category_id": current_category.category_id,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)

        await db.rollback()
        raise ex


async def delete_category(category: GetCategoryId, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        error = {
            "event": "Delete category by id failed",
            "method": "POST",
            "error": "Not authorized to delete category by id",
            "path": "/categories/delete_category",
            "user_id": current_user.user_id,
            "category_id": category.category_id,
            "status_code": 403
        }
        logger.error(error)
        raise HTTPException(
            status_code=403, detail='Not authorized for deleting category.')
    try:
        result = await db.execute(select(Category).where(
            Category.category_id == category.category_id))

        searched_category = result.scalar_one_or_none()

        if searched_category is None:
            raise HTTPException(
                status_code=404, detail=f'Category {category.category_id} not found.')

        await db.delete(searched_category)
        await db.commit()

        end_time = datetime.now(UTC)
        info = {
            "event": "Delete category by id succeeded",
            "method": "POST",
            "path": "/categories/delete_category",
            "user_id": current_user.user_id,
            "deleted_category": category.category_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return {"message": f"Category {category.category_id} deleted successfully."}

    except Exception as ex:
        end_time = datetime.now(UTC)
        error = {
            "event": "Delete category by id failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/categories/delete_category",
            "user_id": current_user.user_id,
            "category_id": category.category_id,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)

        await db.rollback()
        raise ex
