from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import selectinload
from models.orders import Order
from schemas.orders import OrderUpdateById, OrderCreate, OrderUpdateByStatus, OrderStatus, PaymentMethod, FullOrderResponse, FilterOrderInfo, GetOrderInfo, ReservationStatus
from models.people import Person
from models.products import Product
from models.order_items import OrderItems
from models.payment_history import PaymentHistory
from schemas.payment_history import PaymentStatus
from schemas.people import Roles
from models.discount import Discount
from schemas.discount import DiscountType
from schemas.wallet import SortOrder, UpdateWalletAmount
from models.discount_granted import DiscountGranted
from datetime import date
from decimal import Decimal
from math import ceil
from crud.wallet import deduct_from_wallet, update_wallet_amount, make_json_format
import logging
from crud.audit_log import create_audit_log
from schemas.audit import AuditContext

logger = logging.getLogger(__name__)


allowed_statuses = {OrderStatus.UNCONFIRMED: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
                    OrderStatus.CONFIRMED: {OrderStatus.CANCELLED, OrderStatus.PENDING},
                    OrderStatus.PENDING: {OrderStatus.CANCELLED, OrderStatus.DELIVERED},
                    OrderStatus.DELIVERED: {OrderStatus.REFUND_DELIVERED},
                    OrderStatus.CANCELLED: {},
                    OrderStatus.REFUND_DELIVERED: {}}


async def decrease_order_products(db: AsyncSession, order: Order):
    for item in order.order_items:
        if order.reservation_status == ReservationStatus.EXPIRED:
            result = await db.execute(select(Product).where(Product.product_id == item.product_id).with_for_update())
            product = result.scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=404, detail=f"Product {item.product_id} not found")

            if product.remain_in_stock < item.quantity:
                raise HTTPException(
                    status_code=400, detail=f"Product {product.product_name} doesn't have enough amount")

            product.remain_in_stock -= item.quantity

        elif order.reservation_status == ReservationStatus.ACTIVE:
            result = await db.execute(select(Product).where(Product.product_id == item.product_id).with_for_update())
            product = result.scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=404, detail=f"Product {item.product_id} not found")

            product.reserved -= item.quantity


async def create_order(order: OrderCreate, audit: AuditContext, current_user: Person, db: AsyncSession):
    current_user_id = current_user.user_id
    try:
        current_user_id = current_user.user_id
        new_value = dict()
        discount = None
        if order.discount is not None:
            result = await db.execute(select(Discount).where(
                Discount.discount_name == order.discount))

            discount = result.scalar_one_or_none()

            if discount is not None:
                if discount.expired_at < date.today():
                    discount = None

                else:
                    result = await db.execute(select(DiscountGranted).where(
                        DiscountGranted.discount_id == discount.discount_id, DiscountGranted.user_id == current_user.user_id).with_for_update())

                    discount_people = result.scalar_one_or_none()

                    if discount_people is None or discount_people.used:
                        discount = None

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
        await db.refresh(new_order)

        total_amount = 0
        order_items = []
        products = []

        for item in order.items:
            result = await db.execute(select(Product).where(
                func.lower(Product.product_name) == item.product_name.lower()).with_for_update())

            product = result.scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=403, detail=f'Product {item.product_name} not found.')

            if product.remain_in_stock < item.quantity:
                raise HTTPException(
                    status_code=400, detail=f"Product {item.product_name} doesn't have enough amount.")

            product.reserved += item.quantity
            product.remain_in_stock -= item.quantity

            if product and product.product_id in products:
                for order_item in order_items:
                    if order_item.product_id == product.product_id:
                        order_item.quantity += item.quantity

            else:
                products.append(product.product_id)

                new_order_item = OrderItems(
                    order_id=new_order.order_id,
                    product_id=product.product_id,
                    quantity=item.quantity,
                    unit_price=product.unit_price
                )

                db.add(new_order_item)
                await db.flush()
                await db.refresh(new_order_item)

                new_value.update({column.key: getattr(new_order_item, column.key)
                                 for column in inspect(OrderItems).mapper.column_attrs})

                order_items.append(new_order_item)

            total_amount += product.unit_price * item.quantity

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
            payment_amount=new_order.total_amount_discounted
        )

        if discount is not None:
            discount_people.used = True
            discount_people.used_at = date.today()
            discount_people.order_id = new_order.order_id

        db.add(new_payment_history)
        await db.flush()
        await db.refresh(new_payment_history)

        new_value.update({column.key: str(getattr(new_payment_history, column.key))
                         for column in inspect(PaymentHistory).mapper.column_attrs})

        new_value.update({column.key: getattr(
            new_order, column.key) for column in inspect(Order).mapper.column_attrs})

        new_value = make_json_format(new_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user_id,
            entity_id=None,
            entity_type="order",
            event="ORDER_CREATED",
            old_value=None,
            new_value=new_value
        )
        await db.refresh(new_order)

        return FullOrderResponse(orders=new_order, order_items=order_items)

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        logger.exception(f"Add order failed for user {current_user_id}")
        await db.rollback()
        raise


async def get_all_orders(filter_order: FilterOrderInfo, current_user: Person, db: AsyncSession):
    filters = []
    if current_user.role == Roles.CUSTOMER:
        filters.append(Order.customer_id == current_user.user_id)
    elif current_user.role == Roles.MANAGER or current_user.role == Roles.EMPLOYEE:
        if filter_order.customer_id is not None:
            filters.append(Order.customer_id == filter_order.customer_id)
    if filter_order.order_id is not None:
        filters.append(Order.order_id == filter_order.order_id)
    if filter_order.order_status is not None:
        filters.append(Order.order_status == filter_order.order_status)
    if filter_order.order_date_before_date is not None:
        filters.append(Order.order_date <= filter_order.order_date_before_date)
    if filter_order.order_date_after_date is not None:
        filters.append(Order.order_date >= filter_order.order_date_after_date)
    if filter_order.min_total_amount_without_discount is not None:
        filters.append(Order.total_amount_without_discount >=
                       filter_order.min_total_amount_without_discount)
    if filter_order.max_total_amount_discounted is not None:
        filters.append(Order.total_amount_discounted <=
                       filter_order.max_total_amount_discounted)
    if filter_order.payment_method is not None:
        filters.append(Order.payment_method == filter_order.payment_method)

    query = select(Order).where(*filters)
    result = select(func.count()).select_from(query.subquery())
    total = await db.scalar(result)
    offset = (filter_order.page - 1) * filter_order.page_size

    if filter_order.sort_order == SortOrder.ASC:
        query = query.order_by(asc(filter_order.sort_by)).offset(
            offset).limit(filter_order.page_size)
    if filter_order.sort_order == SortOrder.DES:
        query = query.order_by(desc(filter_order.sort_by)).offset(
            offset).limit(filter_order.page_size)

    result = await db.execute(query)
    orders = result.scalars().all()

    if not orders:
        raise HTTPException(status_code=404, detail='No order found.')

    responses = []
    for order in orders:
        result = await db.execute(select(OrderItems).where(OrderItems.order_id == order.order_id))
        order_items = result.scalars().all()

        if not order_items:
            raise HTTPException(
                status_code=404, detail=f"Order_items for order {order.order_id} not found")

        responses.append(FullOrderResponse(
            orders=order, order_items=order_items))

    return GetOrderInfo(orders=responses, page=filter_order.page, page_size=filter_order.page_size, total=total, pages=ceil(total/filter_order.page_size))


async def update_order(current_order: OrderUpdateById, new_order: OrderUpdateByStatus, audit: AuditContext, current_user: Person, db: AsyncSession):
    try:
        old_value = dict()
        new_value = dict()
        result = await db.execute(select(Order).options(selectinload(Order.order_items)).where(
            Order.order_id == current_order.order_id).with_for_update())

        order = result.scalar_one_or_none()

        if order is None:
            raise HTTPException(status_code=404, detail='Order not found')

        if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
            if order.customer_id != current_user.user_id:
                raise HTTPException(status_code=404, detail='Order not found')

            if order.order_status != OrderStatus.UNCONFIRMED:
                raise HTTPException(
                    status_code=400, detail="Don't have premission to change the status")

            if new_order.order_status not in allowed_statuses[order.order_status]:
                raise HTTPException(
                    status_code=400, detail=f"Can't change order status from {order.order_status} to {new_order.order_status}")

            old_value.update({column.key: getattr(order, column.key)
                             for column in inspect(Order).mapper.column_attrs})

            order.order_status = new_order.order_status
            await db.flush()

            new_value.update({column.key: getattr(order, column.key)
                             for column in inspect(Order).mapper.column_attrs})

            result = await db.execute(select(PaymentHistory).where(
                PaymentHistory.order_id == order.order_id).with_for_update())

            payment_history = result.scalar_one_or_none()

            if payment_history is None:
                raise HTTPException(
                    status_code=404, detail=f'Payment history not found for user {current_user.first_name} {current_user.last_name}')

            if new_order.order_status == OrderStatus.CANCELLED:
                old_value.update({column.key: getattr(payment_history, column.key)
                                 for column in inspect(PaymentHistory).mapper.column_attrs})

                payment_history.payment_status = PaymentStatus.CANCELLED
                await db.flush()

                new_value.update({column.key: getattr(payment_history, column.key)
                                 for column in inspect(PaymentHistory).mapper.column_attrs})

                if order.discount:
                    result = await db.execute(select(DiscountGranted).where(
                        DiscountGranted.user_id == order.customer_id, DiscountGranted.discount_id == order.discount).with_for_update())
                    discount = result.scalar_one_or_none()

                    if discount is None:
                        raise HTTPException(
                            status_code=404, detail=f"Discount {order.discount} not found")

                    old_value.update({column.key: getattr(discount, column.key)
                                     for column in inspect(Discount).mapper.column_attrs})

                    discount.used = False
                    discount.used_at = None
                    await db.flush()

                    new_value.update({column.key: getattr(discount, column.key)
                                     for column in inspect(Discount).mapper.column_attrs})

                if order.reservation_status == ReservationStatus.ACTIVE:
                    result = await db.execute(select(OrderItems).where(OrderItems.order_id == order.order_id).with_for_update())
                    cancelled_order_items = result.scalars().all()
                    for order_item in cancelled_order_items:
                        result = await db.execute(select(Product).where(Product.product_id == order_item.product_id).with_for_update())
                        product = result.scalar_one_or_none()

                        if product is None:
                            raise HTTPException(
                                status_code=404, detail=f"The product with id {order_item.product_id} not found")

                        product.reserved -= order_item.quantity
                        product.remain_in_stock += order_item.quantity

                    order.reservation_status = ReservationStatus.EXPIRED

            if new_order.order_status == OrderStatus.CONFIRMED and order.payment_method == PaymentMethod.WALLET:
                await decrease_order_products(db, order)
                await db.flush()

                result = await db.execute(select(Person).where(Person.user_id == order.customer_id))
                user = result.scalar_one_or_none()

                await deduct_from_wallet(
                    UpdateWalletAmount(user_id=user.user_id, amount=order.total_amount_discounted), audit, user, db)

                old_value.update({column.key: getattr(payment_history, column.key)
                                 for column in inspect(PaymentHistory).mapper.column_attrs})

                payment_history.payment_date = date.today()
                payment_history.payment_status = PaymentStatus.SUCCESS
                await db.flush()

                new_value.update({column.key: getattr(payment_history, column.key)
                                 for column in inspect(PaymentHistory).mapper.column_attrs})

            result = await db.execute(select(OrderItems).where(
                OrderItems.order_id == order.order_id))
            order_items = result.scalars().all()

            if not order_items:
                raise HTTPException(
                    status_code=404, detail=f"order_items not found for {order.order_id}")

            new_value = make_json_format(new_value)
            old_value = make_json_format(old_value)

            await create_audit_log(
                db=db,
                audit=audit,
                user_id=current_user.user_id,
                entity_id=current_order.order_id,
                entity_type="order",
                event="ORDER_UPDATED",
                old_value=old_value,
                new_value=new_value
            )

            await db.commit()
            await db.refresh(order)
            return FullOrderResponse(orders=order, order_items=order_items)

        if new_order.order_status not in allowed_statuses[order.order_status]:
            raise HTTPException(
                status_code=400, detail=f"Can't change order status from {order.order_status} to {new_order.order_status}")

        result = await db.execute(select(PaymentHistory).where(
            PaymentHistory.order_id == order.order_id).with_for_update())
        payment_history = result.scalar_one_or_none()

        if payment_history is None:
            raise HTTPException(
                status_code=404, detail=f'Payment history not found for user {order.customer_id}')

        if new_order.order_status == OrderStatus.CONFIRMED:
            await decrease_order_products(db, order)
            await db.flush()

            if order.payment_method == PaymentMethod.WALLET:
                result = await db.execute(select(Person).where(
                    Person.user_id == order.customer_id))
                user = result.scalar_one_or_none()

                if user is None:
                    raise HTTPException(
                        status_code=404, detail="User not found")

                await deduct_from_wallet(
                    UpdateWalletAmount(user_id=user.user_id, amount=order.total_amount_discounted), audit, user, db)

                old_value.update({column.key: getattr(payment_history, column.key)
                                 for column in inspect(PaymentHistory).mapper.column_attrs})

                payment_history.payment_date = date.today()
                payment_history.payment_status = PaymentStatus.SUCCESS
                await db.flush()

                new_value.update({column.key: getattr(payment_history, column.key)
                                 for column in inspect(PaymentHistory).mapper.column_attrs})

        if new_order.order_status == OrderStatus.CANCELLED:
            if order.order_status == OrderStatus.CONFIRMED or order.order_status == OrderStatus.PENDING:
                result = await db.execute(select(Person).where(
                    Person.user_id == order.customer_id))
                user = result.scalar_one_or_none()

                if user is None:
                    raise HTTPException(
                        status_code=404, detail=f"User with user_id {order.customer_id} not found")

                if payment_history.payment_status == PaymentStatus.SUCCESS:
                    await update_wallet_amount(order.total_amount_discounted, audit, user, db, auto_commit=False)

                for item in order.order_items:
                    result = await db.execute(select(Product).where(
                        Product.product_id == item.product_id).with_for_update())
                    product = result.scalar_one_or_none()

                    if product is None:
                        raise HTTPException(
                            status_code=404, detail=f"Product {item.product_id} not found")

                    product.remain_in_stock += item.quantity
                    await db.flush()

            if order.discount:
                result = await db.execute(select(DiscountGranted).where(DiscountGranted.user_id == order.customer_id, DiscountGranted.discount_id == order.discount).with_for_update())
                discount = result.scalar_one_or_none()

                if discount is None:
                    raise HTTPException(
                        status_code=404, detail=f"Discount {order.discount} not found")

                old_value.update({column.key: getattr(discount, column.key)
                                 for column in inspect(Discount).mapper.column_attrs})

                discount.used = False
                discount.used_at = None

                new_value.update({column.key: getattr(discount, column.key)
                                 for column in inspect(Discount).mapper.column_attrs})

            if order.reservation_status == ReservationStatus.ACTIVE:
                result = await db.execute(select(OrderItems).where(OrderItems.order_id == order.order_id).with_for_update())
                cancelled_order_items = result.scalars().all()
                for order_item in cancelled_order_items:
                    result = await db.execute(select(Product).where(Product.product_id == order_item.product_id).with_for_update())
                    product = result.scalar_one_or_none()

                    if product is None:
                        raise HTTPException(
                            status_code=404, detail=f"The product with id {order_item.product_id} not found")

                    product.reserved -= order_item.quantity
                    product.remain_in_stock += order_item.quantity

                order.reservation_status = ReservationStatus.EXPIRED

            old_value.update({column.key: getattr(payment_history, column.key)
                              for column in inspect(PaymentHistory).mapper.column_attrs})

            payment_history.payment_status = PaymentStatus.CANCELLED
            await db.flush()

            new_value.update({column.key: getattr(payment_history, column.key)
                              for column in inspect(PaymentHistory).mapper.column_attrs})

        if new_order.order_status == OrderStatus.REFUND_DELIVERED:
            if payment_history.payment_status == PaymentStatus.SUCCESS:
                result = await db.execute(select(Person).where(Person.user_id == order.customer_id))
                user = result.scalar_one_or_none()

                if user is None:
                    raise HTTPException(
                        status_code=404, detail="User not found")

                await update_wallet_amount(order.total_amount_discounted, audit, user, db, auto_commit=False)

                old_value.update({column.key: getattr(payment_history, column.key)
                                 for column in inspect(PaymentHistory).mapper.column_attrs})

                payment_history.payment_status = PaymentStatus.REFUND
                await db.flush()

                new_value.update({column.key: getattr(payment_history, column.key)
                                 for column in inspect(PaymentHistory).mapper.column_attrs})

        old_value.update({column.key: getattr(order, column.key)
                         for column in inspect(Order).mapper.column_attrs})

        order.order_status = new_order.order_status
        await db.flush()

        new_value.update({column.key: getattr(order, column.key)
                         for column in inspect(Order).mapper.column_attrs})

        new_value = make_json_format(new_value)
        old_value = make_json_format(old_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=current_order.order_id,
            entity_type="order",
            event="ORDER_UPDATED",
            old_value=old_value,
            new_value=new_value
        )

        await db.commit()
        await db.refresh(order)

        result = await db.execute(select(OrderItems).where(OrderItems.order_id == order.order_id))
        order_items = result.scalars().all()

        if not order_items:
            raise HTTPException(
                status_code=404, detail=f"Order items not found for order {order.order_id}")

        return FullOrderResponse(orders=order, order_items=order_items)

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        logger.exception(f"Update order {current_order.order_id} failed")

        await db.rollback()
        raise


async def cancel_order(order: OrderUpdateById, audit: AuditContext, current_user: Person, db: AsyncSession):
    try:
        old_value = dict()
        new_value = dict()

        result = await db.execute(select(Order).where(
            Order.order_id == order.order_id).with_for_update())

        searched_order = result.scalar_one_or_none()

        if searched_order is None:
            raise HTTPException(
                status_code=404, detail=f'Order not found')

        if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
            if searched_order.order_status != OrderStatus.UNCONFIRMED:
                raise HTTPException(
                    status_code=403, detail='There are no longer permission to cancel the order')

            if searched_order.customer_id != current_user.user_id:
                raise HTTPException(
                    status_code=404, detail=f"The order {order.order_id} not found for {current_user.user_id}")

        result = await db.execute(select(OrderItems).where(
            OrderItems.order_id == searched_order.order_id))

        searched_order_items = result.scalars().all()

        if not searched_order_items:
            raise HTTPException(
                status_code=404, detail=f"Order_items not found for {order.order_id}")

        if searched_order.order_status == OrderStatus.CONFIRMED or searched_order.order_status == OrderStatus.PENDING:
            for order_item in searched_order_items:
                result = await db.execute(select(Product).where(
                    Product.product_id == order_item.product_id).with_for_update())

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
                    DiscountGranted.discount_id == discount.discount_id, DiscountGranted.user_id == searched_order.customer_id).with_for_update())

                discount_people = result.scalar_one_or_none()

                if discount_people:
                    old_value.update({column.key: getattr(discount, column.key)
                                     for column in inspect(Discount).mapper.column_attrs})

                    discount_people.used = False
                    discount_people.used_at = None
                    await db.flush()

                    new_value.update({column.key: getattr(discount, column.key)
                                     for column in inspect(Discount).mapper.column_attrs})

        result = await db.execute(select(PaymentHistory).where(
            PaymentHistory.order_id == searched_order.order_id))
        user_payment_history = result.scalar_one_or_none()

        if user_payment_history is not None:
            if searched_order.order_status == OrderStatus.CONFIRMED or searched_order.order_status == OrderStatus.DELIVERED or searched_order.order_status == OrderStatus.PENDING:
                if user_payment_history.payment_status == PaymentStatus.SUCCESS:
                    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
                        result = await db.execute(select(Person).where(Person.user_id == current_user.user_id))
                    elif current_user.role == Roles.MANAGER and current_user.role == Roles.EMPLOYEE:
                        result = await db.execute(select(Person).where(Person.user_id == searched_order.customer_id))

                    user = result.scalar_one_or_none()

                    if user is None:
                        raise HTTPException(
                            status_code=404, detail=f"User with not found")

                    await update_wallet_amount(searched_order.total_amount_discounted, audit, user, db, auto_commit=False)

                    old_value.update({column.key: getattr(user_payment_history, column.key)
                                     for column in inspect(PaymentHistory).mapper.column_attrs})

                    user_payment_history.payment_status = PaymentStatus.REFUND
                    await db.flush()

                    new_value.update({column.key: getattr(user_payment_history, column.key)
                                     for column in inspect(PaymentHistory).mapper.column_attrs})
            else:
                old_value.update({column.key: getattr(user_payment_history, column.key)
                                  for column in inspect(PaymentHistory).mapper.column_attrs})

                user_payment_history.payment_status = PaymentStatus.CANCELLED
                await db.flush()

                new_value.update({column.key: getattr(user_payment_history, column.key)
                                  for column in inspect(PaymentHistory).mapper.column_attrs})

        searched_order.order_status = OrderStatus.CANCELLED

        new_value = make_json_format(new_value)
        old_value = make_json_format(old_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=order.order_id,
            entity_type="order",
            event="ORDER_CANCELED",
            old_value=old_value,
            new_value=new_value
        )
        await db.commit()

        return {"message": f"Order {order.order_id} cancelled."}

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        logger.exception(f"Cancellation order {order.order_id} failed")

        await db.rollback()
        raise
