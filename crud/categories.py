from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schemas.categories import CategoryBase, CategoryCreate
from models.categories import Categories
from models.people import People
from schemas.people import Roles


async def create_category(category: CategoryCreate, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')
    try:
        new_category = Categories(
            category_name=category.category_name
        )

        db.add(new_category)
        await db.commit()
        await db.refresh(new_category)
        return new_category

    except Exception as ex:
        await db.rollback()
        raise ex


async def get_all_categories(current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')

    result = await db.execute(select(Categories))

    categories = result.scalars().all()

    if categories is None:
        raise HTTPException(status_code=404, detail='No categories added yet')

    return categories


async def get_category_by_id(category: int, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')

    result = await db.execute(select(Categories).where(
        Categories.category_id == category.category_id))

    searched_category = result.scalar_one_or_none()

    if searched_category is None:
        raise HTTPException(
            status_code=404, detail=f'category {category.category_id} not found')

    return searched_category


async def update_category(current_category: CategoryBase, category: CategoryCreate, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER:
        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')
    try:
        result = await db.execute(select(Categories).where(
            Categories.category_name == current_category.category_name))

        searched_category = result.scalar_one_or_none()

        if searched_category is None:
            raise HTTPException(
                status_code=404, detail=f'Category {current_category.category_name} not found.')

        searched_category.category_name = category.category_name

        await db.commit()
        await db.refresh(searched_category)
        return searched_category

    except Exception as ex:
        await db.rollback()
        raise ex


async def delete_category(category: CategoryBase, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')
    try:
        result = await db.execute(select(Categories).where(
            Categories.category_name == category.category_name))

        searched_category = result.scalar_one_or_none()

        if searched_category is None:
            raise HTTPException(
                status_code=404, detail=f'Category {category.category_name} not found.')

        await db.delete(searched_category)
        await db.commit()
        return {"message": f"Category {category.category_name} deleted successfully."}

    except Exception as ex:
        await db.rollback()
        raise ex
