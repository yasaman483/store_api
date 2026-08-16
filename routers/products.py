from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from schemas.products import ProductsCreate, ProductsResponse, ProductsUpdateGet, ProductsUpdateSent, GetProductId, GetProductName
from crud.products import create_product, get_all_products, get_product_by_name, get_product_by_id, update_product, delete_product
from models.people import People
import auth

router = APIRouter(prefix='/products', tags=['Products'])


@router.post('/add_product', response_model=ProductsResponse)
async def add_product(product: ProductsCreate, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await create_product(product, current_user, db)


@router.post('/get_products', response_model=list[ProductsResponse])
async def read_all_product(db: AsyncSession = Depends(get_db)):
    return await get_all_products(db)


@router.post('/get_product_by_name', response_model=ProductsResponse)
async def read_product_by_name(product: GetProductName, db: AsyncSession = Depends(get_db)):
    return await get_product_by_name(product, db)


@router.post('get_product_by_id', response_model=ProductsResponse)
async def read_product_by_id(product: GetProductId, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_product_by_id(product, current_user, db)


@router.put('/edit_product', response_model=ProductsResponse)
async def edit_product(current_product: ProductsUpdateSent, updated_product: ProductsUpdateGet, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_product(current_product, updated_product, current_user, db)


@router.delete('/delete')
async def remove_product(product: ProductsUpdateSent, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await delete_product(product, current_user, db)
