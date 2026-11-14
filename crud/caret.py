from fastapi import HTTPException
from schemas.caret import FilterCaret
from models.people import Person
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.people import Roles
from sqlalchemy import select, func, asc, desc
from sqlalchemy.orm import selectinload
from models.caret import Caret
from schemas.caret import GetCarets
from math import ceil
from schemas.wallet import SortOrder
from models.caret_items import CaretItems
from schemas.caret import CaretResponse


async def get_caret_items(filter_caret: FilterCaret, current_user: Person, db: AsyncSession):
    if current_user.role == Roles.CUSTOMER:
        result = await db.execute(select(Caret).options(selectinload(Caret.caret_items)).where(Caret.user_id == current_user.user_id))
        caret = result.scalar_one_or_none()

        if caret is None:
            raise HTTPException(
                status_code=404, detail=f"Caret not found for user {current_user.user_id}")

        return GetCarets(carets=[caret], page=filter_caret.page, page_size=filter_caret.page_size, total=1, pages=1)

    elif current_user.role == Roles.MANAGER or current_user.role == Roles.EMPLOYEE:
        query = select(Caret).options(selectinload(Caret.caret_items))

        filters = []
        if filter_caret.caret_id is not None:
            filters.append(Caret.caret_id == filter_caret.caret_id)
        if filter_caret.user_id is not None:
            filters.append(Caret.user_id == filter_caret.user_id)
        if filter_caret.product_id is not None:
            filters.append(Caret.caret_items.any(CaretItems.product_id ==
                           filter_caret.product_id))
        if filter_caret.min_quantity is not None:
            filters.append(Caret.caret_items.any(
                CaretItems.quantity >= filter_caret.min_quantity))
        if filter_caret.max_quantity is not None:
            filters.append(Caret.caret_items.any(
                CaretItems.quantity <= filter_caret.max_quantity))
        if filter_caret.min_unit_price is not None:
            filters.append(Caret.caret_items.any(CaretItems.unit_price >=
                           filter_caret.min_unit_price))
        if filter_caret.max_unit_price is not None:
            filters.append(Caret.caret_items.any(CaretItems.unit_price <=
                           filter_caret.max_unit_price))
        if filter_caret.before_date_ is not None:
            filters.append(Caret.caret_items.any(
                CaretItems.date_ <= filter_caret.before_date_))
        if filter_caret.after_date_ is not None:
            filters.append(Caret.caret_items.any(
                CaretItems.date_ >= filter_caret.after_date_))
        if filter_caret.caret_item_status is not None:
            filters.append(Caret.caret_items.any(
                CaretItems.caret_item_status == filter_caret.caret_item_status))

        query = select(Caret).options(
            selectinload(Caret.caret_items)).where(*filters)
        result = select(func.count()).select_from(query.subquery())

        total = await db.scalar(result)
        offset = (filter_caret.page - 1)*filter_caret.page_size

        if filter_caret.sort_order == SortOrder.ASC:
            query = query.order_by(asc(filter_caret.sort_by)).offset(
                offset).limit(filter_caret.page_size)

        elif filter_caret.sort_order == SortOrder.DES:
            query = query.order_by(desc(filter_caret.sort_by)).offset(
                offset).limit(filter_caret.page_size)

        result = await db.execute(query)
        caretes = result.scalars().all()

        if not caretes:
            raise HTTPException(status_code=404, detail="No caret found")

        responses = []
        for caret in caretes:
            responses.append(CaretResponse(caret_items=caret.caret_items,
                             caret_id=caret.caret_id, user_id=caret.user_id))

        return GetCarets(carets=responses, page=filter_caret.page, page_size=filter_caret.page_size, total=total, pages=ceil(total/filter_caret.page_size))
