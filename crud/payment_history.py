from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.payment_history import PaymentHistory
from models.people import Person
from models.orders import Order
from schemas.people import Roles
from schemas.payment_history import GetPaymentHistoryId
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)


async def get_payment_histories(current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        end_time = datetime.now(UTC)
        error = {
            "event": "Get payment histories failed",
            "method": "POST",
            "error": "Not authorized to get payment histories",
            "path": "/payment_history/read_payment_histories",
            "user_id": current_user.user_id,
            "status_code": 403,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)

        result = await db.execute(select(Order).where(
            Order.customer_id == current_user.user_id))

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

        end_time = datetime.now(UTC)
        info = {
            "event": "Get payment histories succeeded",
            "method": "POST",
            "path": "/payment_history/read_payment_histories",
            "user_id": current_user.user_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return payment_histories

    else:
        result = await db.execute(select(PaymentHistory))

        payment_histories = result.scalars().all()

        if not payment_histories:
            raise HTTPException(
                status_code=404, detail="No payment history found")

        end_time = datetime.now(UTC)
        info = {
            "event": "Get payment histories succeeded",
            "method": "POST",
            "path": "/payment_history/read_payment_histories",
            "user_id": current_user.user_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return payment_histories


async def get_payment_history_by_id(payment_history: GetPaymentHistoryId, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        end_time = datetime.now(UTC)
        error = {
            "event": "Get payment history by id failed",
            "method": "POST",
            "error": "Not authorized to get payment history",
            "path": "/payment_history/read_payment_history_by_id",
            "user_id": current_user.user_id,
            "payment_history": payment_history.payment_id,
            "status_code": 403,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(PaymentHistory).where(PaymentHistory.payment_id == payment_history.payment_id))

    searched_payment_history = result.scalar_one_or_none()

    if searched_payment_history is None:
        raise HTTPException(
            status_code=404, detail=f"Payment history {payment_history.payment_id} not found")

    end_time = datetime.now(UTC)
    info = {
        "event": "Get payment history by id succeeded",
        "method": "POST",
        "path": "/payment_history/read_payment_history_by_id",
        "user_id": current_user.user_id,
        "payment_history": payment_history.payment_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return searched_payment_history
