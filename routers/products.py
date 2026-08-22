from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from schemas.products import ProductCreate, ProductResponse, ProductUpdateGet, GetProductId, GetProductName
from crud.products import create_product, get_all_products, get_product_by_name, get_product_by_id, update_product, delete_product
from models.people import Person
import auth

router = APIRouter(prefix='/products', tags=['Products'])


@router.post('/add_product', response_model=ProductResponse)
async def add_product(product: ProductCreate, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await create_product(product, current_user, db)


@router.post('/get_products', response_model=list[ProductResponse])
async def read_all_products(current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_all_products(current_user, db)


@router.post('/get_product_by_name', response_model=ProductResponse)
async def read_product_by_name(product: GetProductName, current_user: Person = Depends(auth.get_current_user),  db: AsyncSession = Depends(get_db)):
    return await get_product_by_name(product, current_user, db)


@router.post('get_product_by_id', response_model=ProductResponse)
async def read_product_by_id(product: GetProductId, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_product_by_id(product, current_user, db)


@router.put('/update_product', response_model=ProductResponse)
async def edit_product(current_product: GetProductId, updated_product: ProductUpdateGet, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_product(current_product, updated_product, current_user, db)


@router.delete('/delete_product')
async def remove_product(product: GetProductId, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await delete_product(product, current_user, db)
