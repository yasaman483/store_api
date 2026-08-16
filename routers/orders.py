from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from crud.orders import create_order, get_all_orders, get_order_by_id, update_order, delete_order
from schemas.orders import OrdersResponse, OrderUpdateById, OrdersCreate, OrderUpdateByStatus
from models.people import People
import auth


router = APIRouter(prefix='/orders', tags=['Orders'])


@router.post('/add_order', response_model=OrdersResponse)
async def add_order(order: OrdersCreate, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await create_order(order, current_user, db)


@router.post('/get_all_orders', response_model=list[OrdersResponse])
async def read_all_orders(current_uer: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_all_orders(current_uer, db)


@router.post('/get_order_by_id', response_model=OrdersResponse)
async def read_order_by_id(order: OrderUpdateById, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_order_by_id(order, current_user, db)


@router.put('/edit_order', response_model=OrdersResponse)
async def edit_order_status(current_order: OrderUpdateById, new_order: OrderUpdateByStatus, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_order(current_order, new_order, current_user, db)


@router.delete('/delete')
async def remove_order(order: OrderUpdateById, current_uer: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await delete_order(order, current_uer, db)
