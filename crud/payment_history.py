from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.payment_history import PaymentHistory
from models.people import People
from models.orders import Orders
from schemas.people import Roles
from schemas.payment_history import GetPaymentHistoryId


async def get_payment_histories(current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        result = await db.execute(select(Orders).where(
            Orders.customer_id == current_user.people_id))

        orders = result.scalars().all()

        if not orders:
            raise HTTPException(
                status_code=404, detail=f"No payment history found for {current_user.first_name} {current_user.last_name}")

        payment_histories = []

        for i in range(len(orders)):
            result = await db.execute(select(PaymentHistory).where(
                PaymentHistory.order_id == orders[i].order_id))

            payment_history = result.scalar_one_or_none()

            if payment_history is None:
                raise HTTPException(
                    status_code=404, detail=f"Payment history for order {orders[i].order_id} not found")

            payment_histories.append(payment_history)

        return payment_histories

    else:
        result = await db.execute(select(PaymentHistory))

        payment_histories = result.scalars().all()

        if not payment_histories:
            raise HTTPException(
                status_code=404, detail="No payment history found")

        return payment_histories


async def get_payment_history_by_id(payment_history: GetPaymentHistoryId, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(PaymentHistory).where(PaymentHistory.payment_id == payment_history.payment_id))

    searched_payment_history = result.scalar_one_or_none()

    if searched_payment_history is None:
        raise HTTPException(
            status_code=404, detail=f"Payment history {payment_history.payment_id} not found")

    return searched_payment_history
