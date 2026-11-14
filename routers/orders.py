from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from crud.orders import get_all_orders, update_order, cancel_order
from schemas.orders import FullOrderResponse, OrderUpdateById, OrderUpdateByStatus, FilterOrderInfo, GetOrderInfo
from models.people import Person
import auth
from crud.audit_log import create_audit_context


router = APIRouter(prefix='/orders', tags=['Orders'])


@router.post('/get_all_orders', response_model=GetOrderInfo)
async def read_all_orders(filter_order: FilterOrderInfo, current_uer: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_all_orders(filter_order, current_uer, db)


@router.patch('/edit_order', response_model=FullOrderResponse)
async def edit_order_status(current_order: OrderUpdateById, new_order: OrderUpdateByStatus, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await update_order(current_order, new_order, audit, current_user, db)


@router.delete('/delete_order')
async def remove_order(order: OrderUpdateById, request: Request, current_uer: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await cancel_order(order, audit, current_uer, db)
