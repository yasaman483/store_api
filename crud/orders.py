from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.orders import Order
from schemas.orders import OrderUpdateById, OrderCreate, OrderUpdateByStatus, OrderStatus
from models.people import Person
from models.products import Product
from models.order_items import OrderItems
from models.payment_history import PaymentHistory
from schemas.orders import OrderStatus
from schemas.payment_history import PaymentStatus
from schemas.people import Roles
from models.discount import Discount
from schemas.discount import DiscountType
from models.discount_granted import DiscountGranted
from datetime import date
from decimal import Decimal
from schemas.orders import PaymentMethod
from crud.wallet import deduct_from_wallet
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)


allowed_statuses = {OrderStatus.UNCONFIRMED: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
                    OrderStatus.CONFIRMED: {OrderStatus.CANCELLED, OrderStatus.PENDING},
                    OrderStatus.PENDING: {OrderStatus.CANCELLED, OrderStatus.DELIVERED}}


async def create_order(order: OrderCreate, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    try:
        discount = None
        if order.discount is not None:
            result = await db.execute(select(Discount).where(
                Discount.discount_name == order.discount))

            discount = result.scalar_one_or_none()

            if discount is not None:
                if discount.expired_at < date.today():
                    raise HTTPException(
                        status_code=400, detail='The discount code expired')

                result = await db.execute(select(DiscountGranted).where(
                    DiscountGranted.discount_id == discount.discount_id, DiscountGranted.people_id == current_user.user_id))

                discount_people = result.scalar_one_or_none()

                if discount_people is None:
                    raise HTTPException(
                        status_code=404, detail=f"The discount code {discount.discount_name} is not available for {current_user.first_name} {current_user.last_name}")

                if discount_people.used:
                    raise HTTPException(
                        status_code=403, detail='The discount code used before')

        new_order = Order(
            customer_id=current_user.user_id,
            order_status=OrderStatus.UNCONFIRMED,
            payment_method=order.payment_method,
            discount=order.discount,
            total_amount_without_discount=0,
            total_amount_discounted=0
        )

        db.add(new_order)
        await db.flush()

        total_amount = 0

        for item in order.items:
            result = await db.execute(select(Product).where(
                Product.product_name == item.product_name))

            product = result.scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=403, detail=f'Product {item.product_name} not found.')

            if product.remain_in_stock < item.quantity:
                raise HTTPException(
                    status_code=400, detail=f"Product {item.product_name} doesn't have enough amount.")

            new_order_item = OrderItems(
                order_id=new_order.order_id,
                product_id=product.product_id,
                quantity=item.quantity,
                unit_price=product.unit_price
            )

            db.add(new_order_item)

            total_amount += product.unit_price * item.quantity
            product.remain_in_stock -= item.quantity

        new_order.total_amount_without_discount = total_amount

        if discount is not None and discount.discount_type == DiscountType.PERCENT:
            new_order.total_amount_discounted = new_order.total_amount_without_discount * \
                (Decimal("100")-discount.amount)/Decimal("100")
        elif discount is not None and discount.discount_type == DiscountType.AMOUNT:
            new_order.total_amount_discounted = new_order.total_amount_without_discount - discount.amount
        elif discount is None:
            new_order.total_amount_discounted = total_amount

        new_order.total_amount_discounted = max(
            Decimal("0"), new_order.total_amount_discounted)

        new_payment_history = PaymentHistory(
            order_id=new_order.order_id,
            payment_status=PaymentStatus.PENDING,
            payment_amount=new_order.total_amount_discounted)

        if discount is not None:
            discount_people.used = True
            discount_people.used_at = date.today()
            discount_people.order_id = new_order.order_id

        db.add(new_payment_history)

        await db.commit()
        await db.refresh(new_order)

        end_time = datetime.now(UTC)
        info = {
            "event": "Add order succeeded",
            "method": "POST",
            "path": "/orders/add_order",
            "user_id": current_user.user_id,
            "added_order": new_order.order_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return new_order

    except Exception as ex:
        end_time = datetime.now(UTC)
        error = {
            "event": "Add order failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/orders/add_order",
            "user_id": current_user.user_id,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        await db.rollback()
        raise ex


async def get_all_orders(current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role == Roles.MANAGER or current_user.role == Roles.EMPLOYEE:
        result = await db.execute(select(Order))

        all_orders = result.scalars().all()

        if not all_orders:
            raise HTTPException(status_code=404, detail='No order found.')

        end_time = datetime.now(UTC)
        info = {
            "event": "Get all orders succeeded",
            "method": "POST",
            "path": "/orders/get_all_orders",
            "user_id": current_user.user_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return all_orders

    result = await db.execute(select(Order).where(
        Order.customer_id == current_user.user_id))

    customer_orders = result.scalars().all()

    if not customer_orders:
        raise HTTPException(
            status_code=404, detail=f"There aren't any orders for {current_user.first_name} {current_user.last_name}")

    end_time = datetime.now(UTC)
    info = {
        "event": "Get all cucstomer's orders succeeded",
        "method": "POST",
        "path": "/orders/get_all_orders",
        "user_id": current_user.user_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return customer_orders


async def get_order_by_id(order: OrderUpdateById, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role == Roles.MANAGER or current_user.role == Roles.EMPLOYEE:
        result = await db.execute(select(Order).where(Order.order_id == order.order_id))

        searched_order = result.scalar_one_or_none()

        if searched_order is None:
            raise HTTPException(status_code=404, detail='No order found.')

        end_time = datetime.now(UTC)
        info = {
            "event": "Get order by id succeeded",
            "method": "POST",
            "path": "/orders/get_order_by_id",
            "user_id": current_user.user_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return searched_order

    result = await db.execute(select(Order).where(
        Order.customer_id == current_user.user_id, Order.order_id == order.order_id))

    customer_order = result.scalar_one_or_none()

    if not customer_order:
        raise HTTPException(
            status_code=404, detail=f"There aren't any orders for {current_user.first_name} {current_user.last_name}")

    end_time = datetime.now(UTC)
    info = {
        "event": "Get customer's order by id succeeded",
        "method": "POST",
        "path": "/orders/get_order_by_id",
        "user_id": current_user.user_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return customer_order


async def update_order(current_order: OrderUpdateById, new_order: OrderUpdateByStatus, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    try:
        result = await db.execute(select(Order).where(
            Order.order_id == current_order.order_id))

        order = result.scalar_one_or_none()

        if order is None:
            raise HTTPException(status_code=404, detail='Order not found')

        if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
            if order.order_status != OrderStatus.UNCONFIRMED:
                raise HTTPException(
                    status_code=400, detail="Don't have premission to change the status")

            if order.customer_id != current_user.user_id:
                raise HTTPException(status_code=404, detail='Order not found')

            if new_order.order_status not in allowed_statuses[order.order_status]:
                raise HTTPException(
                    status_code=400, detail=f"Can't change order status from {new_order.order_status} to {order.order_status}")

            order.order_status = new_order.order_status

            result = await db.execute(select(PaymentHistory).where(
                PaymentHistory.order_id == order.order_id))

            payment_history = result.scalar_one_or_none()

            if payment_history is None:
                raise HTTPException(
                    status_code=404, detail=f'Payment history not found for user {current_user.first_name} {current_user.last_name}')

            if order.payment_method == PaymentMethod.WALLET:
                try:
                    await deduct_from_wallet(
                        order.total_amount_discounted, current_user, db)

                    payment_history.payment_date = date.today()
                    payment_history.payment_status = PaymentStatus.SUCCESS

                except Exception as e:
                    end_time = datetime.now(UTC)
                    error = {
                        "event": "Update order failed",
                        "method": "POST",
                        "error": f"{ex}",
                        "path": "/orders/edit_order",
                        "user_id": current_user.user_id,
                        "duration": (end_time - start_time).total_seconds()
                    }
                    logger.error(error)

                    payment_history.payment_status = PaymentStatus.FAILED
                    raise e

            await db.commit()
            await db.refresh(order)
            return order

        if new_order.order_status not in allowed_statuses[order.order_status]:
            raise HTTPException(
                status_code=400, detail=f"Can't change order status from {order.order_status} to {new_order.order_status}")

        order.order_status = new_order.order_status

        await db.commit()
        await db.refresh(order)

        end_time = datetime.now(UTC)
        info = {
            "event": "Update order succeeded",
            "method": "POST",
            "path": "/orders/edit_order",
            "user_id": current_user.user_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return order

    except Exception as ex:
        end_time = datetime.now(UTC)
        error = {
            "event": "Update order failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/orders/edit_order",
            "user_id": current_user.user_id,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)

        await db.rollback()
        raise ex


async def delete_order(order: OrderUpdateById, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    try:
        result = await db.execute(select(Order).where(
            Order.order_id == order.order_id))

        searched_order = result.scalar_one_or_none()

        if searched_order is None:
            raise HTTPException(
                status_code=404, detail=f'Order not found')

        if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
            if searched_order.order_status != OrderStatus.UNCONFIRMED:
                raise HTTPException(
                    status_code=403, detail='There are no longer permission to delete the order')

            if searched_order.customer_id != current_user.user_id:
                error = {
                    "event": "Delete order failed",
                    "method": "POST",
                    "error": "Not authorized to delete order.",
                    "path": "/products/delete_order",
                    "user_id": current_user.user_id,
                    "order_id": searched_order.order_id,
                    "status_code": 403
                }
                logger.error(error)

                raise HTTPException(
                    status_code=403, detail='Not authorized to change the specified order status.')

        result = await db.execute(select(OrderItems).where(
            OrderItems.order_id == searched_order.order_id))

        searched_order_items = result.scalars().all()

        for order_item in searched_order_items:
            result = await db.execute(select(Product).where(
                Product.product_id == order_item.product_id))

            product = result.scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=404, detail=f"Product {order_item.product_id} not found")

            product.remain_in_stock += order_item.quantity

        if searched_order.discount:
            result = await db.execute(select(Discount).where(
                Discount.discount_name == searched_order.discount))

            discount = result.scalar_one_or_none()

            if discount:
                result = await db.execute(select(DiscountGranted).where(
                    DiscountGranted.discount_id == discount.discount_id, DiscountGranted.people_id == current_user.people_id))

                discount_people = result.scalar_one_or_none()

                if discount_people:
                    discount_people.used = False
                    discount_people.used_at = None

        result = await db.execute(select(PaymentHistory).where(
            PaymentHistory.order_id == searched_order.order_id))

        user_payment_history = result.scalar_one_or_none()

        if user_payment_history:
            await db.delete(user_payment_history)
            await db.flush()

        await db.delete(searched_order)
        await db.commit()

        end_time = datetime.now(UTC)
        info = {
            "event": "Delete order succeeded",
            "method": "POST",
            "path": "/orders/delete_order",
            "user_id": current_user.user_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return {"message": f"Order {order.order_id} deleted."}

    except Exception as ex:
        end_time = datetime.now(UTC)
        error = {
            "event": "Delete order failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/orders/delete_order",
            "user_id": current_user.user_id,
            "order_id": order.order_id,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)

        db.rollback()
        raise ex
