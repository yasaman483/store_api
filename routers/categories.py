from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from schemas.categories import CategoryBase, CategoryCreate, CategoryResponse, GetCategoryId
from crud.categories import create_category, get_all_categories, update_category, delete_category, get_category_by_id
from models.people import Person
import auth

router = APIRouter(prefix='/categories', tags=['Categories'])


@router.post('/add_category', response_model=CategoryResponse)
async def add_catgory(category: CategoryCreate, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await create_category(category, current_user, db)


@router.post('/get_categories', response_model=list[CategoryResponse])
async def read_all_categories(current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_all_categories(current_user, db)


@router.post('/get_category', response_model=CategoryResponse)
async def read_category_by_id(category: GetCategoryId, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_category_by_id(category, current_user, db)


@router.put('/edit_category', response_model=CategoryResponse)
async def edit_category(current_categor: GetCategoryId, category: CategoryCreate, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_category(current_categor, category, current_user, db)


@router.delete('/delete_category')
async def remove_category(category: GetCategoryId, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await delete_category(category, current_user, db)
