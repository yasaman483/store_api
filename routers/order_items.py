from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from crud.order_items import update_order_item, delete_order_item
from schemas.order_items import OrderItemsResponse, OrderItemsUpdate, OrderItemsDelete
from schemas.orders import OrderUpdateById
from models.people import Person
import auth
import logging
from crud.audit_log import create_audit_context


logger = logging.getLogger(__name__)


router = APIRouter(prefix='/order_items', tags=['OrderItems'])


@router.patch('/update_order_item', response_model=list[OrderItemsResponse])
async def edit_order_item(order: OrderUpdateById, order_items: list[OrderItemsUpdate], request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await update_order_item(order, order_items, audit, current_user, db)


@router.delete('/delete_order_item')
async def remove_order_item(order: OrderUpdateById, order_items: list[OrderItemsDelete], request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await delete_order_item(order, order_items, audit, current_user, db)
