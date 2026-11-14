from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from schemas.categories import CategoryCreate, CategoryResponse, GetCategoryId, CategoryUpdate, GetCategoryInfo, FilterCategory
from crud.categories import create_category, get_all_categories, update_category, unactive_category
from models.people import Person
import auth
from crud.audit_log import create_audit_context

router = APIRouter(prefix='/categories', tags=['Categories'])


@router.post('/add_category', response_model=CategoryResponse)
async def add_catgory(category: CategoryCreate, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await create_category(category, audit, current_user, db)


@router.post('/get_categories', response_model=GetCategoryInfo)
async def read_all_categories(request: Request, filter_category: FilterCategory, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await get_all_categories(audit, filter_category, current_user, db)


@router.patch('/edit_category', response_model=CategoryResponse)
async def edit_category(current_categor: GetCategoryId, category: CategoryUpdate, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await update_category(current_categor, category, audit, current_user, db)


@router.delete('/unactive_category')
async def remove_category(category: GetCategoryId, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await unactive_category(category, audit, current_user, db)
