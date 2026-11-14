from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.connect import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from models.orders import Order
from schemas.orders import ReservationStatus
from datetime import datetime, UTC
from models.products import Product


async def release_reservations(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Order).options(selectinload(Order.order_items)).where(Order.reservation_status == ReservationStatus.ACTIVE))
    orders = result.scalars().all()

    for order in orders:
        if order.expired_reservation_at >= datetime.now(UTC):
            for order_item in order.order_items:
                result = await db.execute(select(Product).where(Product.product_id == order_item.product_id))
                product = result.scalar_one_or_none()

                if product is None:
                    raise HTTPException(
                        status_code=404, detail=f"The product with id {order_item.product_id} not found")

                product.reserved -= order_item.quantity
                product.remain_in_stock += order_item.quantity

        order.reservation_status = ReservationStatus.EXPIRED

    await db.commit()
