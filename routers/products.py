from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from schemas.products import ProductCreate, ProductResponse, ProductUpdateGet, GetProductId, FilterProduct, GetProduct
from crud.products import create_product, get_all_products, update_product, unactive_product
from models.people import Person
import auth
from crud.audit_log import create_audit_context

router = APIRouter(prefix='/products', tags=['Products'])


@router.post('/add_product', response_model=ProductResponse)
async def add_product(product: ProductCreate, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await create_product(product, audit, current_user, db)


@router.post('/get_products', response_model=GetProduct)
async def read_all_products(filter_products: FilterProduct, db: AsyncSession = Depends(get_db)):
    return await get_all_products(filter_products, db)


@router.patch('/update_product', response_model=ProductResponse)
async def edit_product(current_product: GetProductId, updated_product: ProductUpdateGet, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await update_product(current_product, updated_product, audit, current_user, db)


@router.delete('/delete_product')
async def remove_product(product: GetProductId, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await unactive_product(product, audit, current_user, db)
