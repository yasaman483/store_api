from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from crud.order_items import get_order_items, update_order_item, delete_order_item
from schemas.order_items import OrderItemsResponse, OrderItemsUpdate, OrderItemsDelete
from schemas.orders import OrderUpdateById
from models.people import Person
import auth
import logging


logger = logging.getLogger(__name__)


router = APIRouter(prefix='/order_items', tags=['OrderItems'])


@router.post('/get_order_items', response_model=list[OrderItemsResponse])
async def read_all_order_items(order: OrderUpdateById, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_order_items(order, current_user, db)


@router.put('/update_order_item', response_model=list[OrderItemsResponse])
async def edit_order_item(order: OrderUpdateById, order_items: list[OrderItemsUpdate], current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_order_item(order, order_items, current_user, db)


@router.delete('/delete_order_item')
async def remove_order_item(order: OrderUpdateById, order_items: list[OrderItemsDelete], current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await delete_order_item(order, order_items, current_user, db)
