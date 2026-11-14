from models.people import Person
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc
from models.discount_granted import DiscountGranted
from fastapi import HTTPException
from schemas.people import Roles
from schemas.discount_granted import DiscountGrantedFilter, GetDiscountGranted
import logging
from schemas.wallet import SortOrder
from math import ceil

logger = logging.getLogger(__name__)


async def get_discount_granted(filter_discount: DiscountGrantedFilter, current_user: Person, db: AsyncSession):
    if current_user.role == Roles.CUSTOMER:
        query = select(DiscountGranted).where(
            DiscountGranted.user_id == current_user.user_id)

        result = select(func.count()).select_from(query.subquery())
        total = await db.scalar(result)

        result = await db.execute(query)
        discounts = result.scalars().all()

        return GetDiscountGranted(discount_granted=discounts, page=filter_discount.page, page_size=filter_discount.page_size, total=total, pages=ceil(total/filter_discount.page_size))

    elif current_user.role == Roles.MANAGER or current_user.role == Roles.EMPLOYEE:
        filters = []
        if filter_discount.discount_id is not None:
            filters.append(DiscountGranted.discount_id ==
                           filter_discount.discount_id)
        if filter_discount.order_id is not None:
            filters.append(DiscountGranted.order_id ==
                           filter_discount.order_id)
        if filter_discount.user_id is not None:
            filters.append(DiscountGranted.user_id == filter_discount.user_id)
        if filter_discount.used is not None:
            filters.append(DiscountGranted.used == filter_discount.used)
        if filter_discount.used_at is not None:
            filters.append(DiscountGranted.used_at == filter_discount.used_at)

        query = select(DiscountGranted).where(*filters)
        result = select(func.count()).select_from(query.subquery())
        total = await db.scalar(result)
        offset = (filter_discount.page - 1)*filter_discount.page_size

        if filter_discount.sort_order == SortOrder.ASC:
            query = query.order_by(asc(filter_discount.sort_by)).offset(
                offset).limit(filter_discount.page_size)

        elif filter_discount.sort_order == SortOrder.DES:
            query = query.order_by(desc(filter_discount.sort_by)).offset(
                offset).limit(filter_discount.page_size)

        result = await db.execute(query)
        discount_granted = result.scalars().all()

        if not discount_granted:
            raise HTTPException(
                status_code=404, detail="No discount granted found")

        return GetDiscountGranted(discount_granted=discount_granted, page=filter_discount.page, page_size=filter_discount.page_size, total=total, pages=ceil(total/filter_discount.page_size))
