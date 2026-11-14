from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, desc, func
from sqlalchemy.orm import selectinload
from models.payment_history import PaymentHistory
from models.people import Person
from models.orders import Order
from schemas.people import Roles
from schemas.payment_history import FilterPaymentHistory, GetPaymentHistory
from schemas.wallet import SortOrder
from math import ceil
import logging

logger = logging.getLogger(__name__)


async def get_payment_histories(filter_payment_history: FilterPaymentHistory, current_user: Person, db: AsyncSession):
    filters = []
    if filter_payment_history.payment_status is not None:
        filters.append(PaymentHistory.payment_status ==
                       filter_payment_history.payment_status)
    if filter_payment_history.min_payment_amount is not None:
        filters.append(PaymentHistory.payment_amount >=
                       filter_payment_history.min_payment_amount)
    if filter_payment_history.max_payment_amount is not None:
        filters.append(PaymentHistory.payment_amount <=
                       filter_payment_history.max_payment_amount)
    if filter_payment_history.payment_after_date is not None:
        filters.append(PaymentHistory.payment_date >=
                       filter_payment_history.payment_after_date)
    if filter_payment_history.payment_befor_date is not None:
        filters.append(PaymentHistory.payment_date <=
                       filter_payment_history.payment_befor_date)

    if current_user.role == Roles.CUSTOMER:
        if filter_payment_history.order_id is not None:
            filters.append(PaymentHistory.order.has(
                Order.order_id == filter_payment_history.order_id))
        if filter_payment_history.payment_id is not None:
            filters.append(PaymentHistory.payment_id ==
                           filter_payment_history.payment_id)

    elif current_user.role == Roles.MANAGER or current_user.role == Roles.EMPLOYEE:
        if filter_payment_history.order_id is not None:
            filters.append(PaymentHistory.order_id ==
                           filter_payment_history.order_id)
        if filter_payment_history.payment_id is not None:
            filters.append(PaymentHistory.payment_id ==
                           filter_payment_history.payment_id)

    query = select(PaymentHistory).options(
        selectinload(PaymentHistory.order)).where(*filters)

    result = select(func.count()).select_from(query.subquery())
    total = await db.scalar(result)
    offset = (filter_payment_history.page - 1)*filter_payment_history.page_size

    if filter_payment_history.sort_order == SortOrder.ASC:
        query = query.order_by(asc(filter_payment_history.sort_by)).offset(
            offset).limit(filter_payment_history.page_size)

    if filter_payment_history.sort_order == SortOrder.DES:
        query = query.order_by(desc(filter_payment_history.sort_by)).offset(
            offset).limit(filter_payment_history.page_size)

    result = await db.execute(query)

    payment_histories = result.scalars().all()

    if not payment_histories:
        raise HTTPException(
            status_code=404, detail="No payment history found")

    return GetPaymentHistory(payment_histories=payment_histories, page=filter_payment_history.page, page_size=filter_payment_history.page_size, total=total, pages=ceil(total/filter_payment_history.page_size))
