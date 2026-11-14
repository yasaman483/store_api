from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.inspection import inspect
from models.people import Person
from models.order_items import OrderItems
from models.orders import Order
from schemas.order_items import OrderItemsUpdate, OrderItemsDelete
from schemas.orders import OrderStatus, OrderUpdateById
from models.products import Product
from models.discount import Discount
from models.discount_granted import DiscountGranted
from schemas.discount import DiscountType
from decimal import Decimal
from models.payment_history import PaymentHistory
import logging
from crud.audit_log import create_audit_log
from schemas.audit import AuditContext
from schemas.people import Roles

logger = logging.getLogger(__name__)


async def update_order_item(order: OrderUpdateById, order_items: list[OrderItemsUpdate], audit: AuditContext, current_user: Person, db: AsyncSession):
    try:
        new_value = dict()
        old_value = dict()
        counter = 0
        result = await db.execute(select(Order).where(
            Order.order_id == order.order_id).with_for_update())

        searched_order = result.scalar_one_or_none()

        if searched_order is None:
            raise HTTPException(status_code=404, detail='No order found')

        if searched_order.customer_id != current_user.user_id and current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
            raise HTTPException(
                status_code=404, detail="Order not found")

        if searched_order.order_status != OrderStatus.UNCONFIRMED:
            raise HTTPException(
                status_code=400, detail='Not allowed to update the order anymore')

        products = dict()
        for i in range(len(order_items)):
            if products and order_items[i].product_name in products.keys():
                products[order_items[i].product_name].append(i)
            else:
                products[order_items[i].product_name] = [i]

        for ordered_product in products.keys():
            total_quantity = 0
            if len(products[ordered_product]) > 1:
                for i in products[ordered_product]:
                    total_quantity += order_items[i].quantity
                    if i != min(products[ordered_product]):
                        order_items[i] = "None"

                    order_items[min(products[ordered_product])
                                ].quantity = total_quantity

        for item in order_items:
            if item == "None":
                order_items.remove(item)

        updated_list = []
        total_amount = Decimal("0")
        for i in range(len(order_items)):
            result = await db.execute(select(Product).where(
                func.lower(Product.product_name) == order_items[i].product_name.lower()))

            product = result.scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=404, detail='Product not found')

            result = await db.execute(select(OrderItems).where(
                OrderItems.order_id == order.order_id, OrderItems.product_id == product.product_id).with_for_update())

            searched_order_item = result.scalar_one_or_none()

            if searched_order_item is None:
                if product.remain_in_stock < order_items[i].quantity:
                    raise HTTPException(
                        status_code=400, detail=f"Product {product.product_name} doesn't have enough amount.")

                counter += 1
                new_order_item = OrderItems(
                    order_id=order.order_id,
                    product_id=product.product_id,
                    quantity=order_items[i].quantity,
                    unit_price=product.unit_price
                )

                total_amount += order_items[i].quantity*product.unit_price

                db.add(new_order_item)
                await db.flush()

                new_value[f"new_order_item{counter}"] = {column.key: getattr(
                    new_order_item, column.key) for column in inspect(OrderItems).mapper.column_attrs}

                await db.refresh(new_order_item)
                updated_list.append(new_order_item)
                continue

            if (order_items[i].quantity-searched_order_item.quantity) > product.remain_in_stock:
                raise HTTPException(
                    status_code=400, detail=f"Product {product.product_name} doesn't have enough amount.")

            if order_items[i].quantity > searched_order_item.quantity:
                total_amount += (order_items[i].quantity -
                                 searched_order_item.quantity)*product.unit_price

            if order_items[i].quantity < searched_order_item.quantity:
                total_amount += (order_items[i].quantity -
                                 searched_order_item.quantity)*product.unit_price

            old_value[f"existed order for product {product.product_id}"] = {column.key: getattr(
                searched_order_item, column.key) for column in inspect(OrderItems).mapper.column_attrs}

            searched_order_item.quantity = order_items[i].quantity
            await db.flush()

            new_value[f"existed order for product {product.product_id}"] = {column.key: getattr(
                searched_order_item, column.key) for column in inspect(OrderItems).mapper.column_attrs}

            updated_list.append(searched_order_item)
            await db.refresh(searched_order_item)

        old_value[f"order {searched_order.order_id}"] = {column.key: getattr(
            searched_order, column.key) for column in inspect(Order).mapper.column_attrs}

        if searched_order.discount:
            result = await db.execute(select(Discount).where(
                Discount.discount_name == searched_order.discount))

            discount = result.scalar_one_or_none()

            if discount:
                result = await db.execute(select(DiscountGranted).where(DiscountGranted.discount_id ==
                                                                        discount.discount_id, DiscountGranted.order_id == order.order_id).with_for_update())

                person_discount = result.scalar_one_or_none()

                if person_discount:
                    if discount.discount_type == DiscountType.PERCENT:
                        searched_order.total_amount_discounted = searched_order.total_amount_without_discount * \
                            (Decimal("100")-discount.amount)/Decimal("100")
                    else:
                        searched_order.total_amount_discounted = searched_order.total_amount_without_discount - discount.amount

                    searched_order.total_amount_discounted = max(
                        Decimal("0"), searched_order.total_amount_discounted)
        else:
            searched_order.total_amount_discounted = searched_order.total_amount_without_discount

        await db.flush()
        new_value[f"order {searched_order.order_id}"] = {column.key: getattr(
            searched_order, column.key) for column in inspect(Order).mapper.column_attrs}

        result = await db.execute(select(PaymentHistory).where(
            PaymentHistory.order_id == order.order_id).with_for_update())

        payment_history = result.scalar_one_or_none()

        if payment_history is None:
            raise HTTPException(
                status_code=404, detail=f"No payment history found for order {searched_order.order_id}")

        payment_history.payment_amount = searched_order.total_amount_discounted

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=order.order_id,
            entity_type="order",
            event="ORDER_ITEM_UPDATED",
            old_value=old_value,
            new_value=new_value
        )

        await db.commit()
        return updated_list

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        logger.error(f"Update order {order.order_id} items failed")

        await db.rollback()
        raise


async def delete_order_item(order: OrderUpdateById, order_items: list[OrderItemsDelete], audit: AuditContext, current_user: Person, db: AsyncSession):
    try:
        old_value = dict()
        new_value = dict()
        result = await db.execute(select(Order).where(
            Order.order_id == order.order_id).with_for_update())

        searched_order = result.scalar_one_or_none()

        if searched_order is None:
            raise HTTPException(status_code=404, detail='No order item found')

        if searched_order.customer_id != current_user.user_id and current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
            raise HTTPException(
                status_code=404, detail=f"Order {order.order_id} not found")

        if searched_order.order_status != OrderStatus.UNCONFIRMED:
            raise HTTPException(
                status_code=400, detail='Not allowed to change the order anymore')

        for i in range(len(order_items)):
            result = await db.execute(select(Product).where(
                func.lower(Product.product_name) == order_items[i].product_name.lower()))

            product = result.scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=404, detail='Product not found')

            result = await db.execute(select(OrderItems).where(
                OrderItems.order_id == order.order_id, OrderItems.product_id == product.product_id).with_for_update())

            searched_order_item = result.scalar_one_or_none()

            if searched_order_item is None:
                raise HTTPException(
                    status_code=404, detail='Order item not found')

            old_value.update({column.key: getattr(searched_order_item, column.key)
                             for column in inspect(Order).mapper.column_attrs})

            searched_order.total_amount_without_discount -= searched_order_item.quantity * \
                searched_order_item.unit_price

            await db.flush()
            new_value.update({column.key: getattr(searched_order_item, column.key)
                             for column in inspect(Order).mapper.column_attrs})

            await db.delete(searched_order_item)

        await db.flush()

        result = await db.execute(select(func.count()).select_from(OrderItems).where(
            OrderItems.order_id == order.order_id).with_for_update())

        remaining_items = result.scalar_one()

        if remaining_items == 0:
            await db.delete(order)
            if searched_order.discount:
                result = await db.execute(select(Discount).where(
                    Discount.discount_name == searched_order.discount))

                user_discount = result.scalar_one_or_none()

                if user_discount:
                    result = await db.execute(select(DiscountGranted).where(DiscountGranted.discount_id ==
                                                                            user_discount.discount_id, DiscountGranted.order_id == order.order_id).with_for_update())
                    person_discount = result.scalar_one_or_none()

                    if person_discount:
                        old_value.update({column.key: getattr(
                            person_discount, column.key) for column in inspect(Discount).mapper.column_attrs})

                        person_discount.used = False
                        person_discount.used_at = None
                        await db.flush()

                        new_value.update({column.key: getattr(
                            person_discount, column.key) for column in inspect(Discount).mapper.column_attrs})

        elif searched_order.discount:
            result = await db.execute(select(Discount).where(
                Discount.discount_name == searched_order.discount))

            discount = result.scalar_one_or_none()

            if discount:
                result = await db.execute(select(DiscountGranted).where(DiscountGranted.discount_id ==
                                                                        discount.discount_id, DiscountGranted.order_id == order.order_id).with_for_update())
                person_discount = result.scalar_one_or_none()

                if person_discount:
                    old_value.update({column.key: getattr(
                        searched_order, column.key) for column in inspect(Order).mapper.column_attrs})

                    if discount.discount_type == DiscountType.PERCENT:
                        searched_order.total_amount_discounted = searched_order.total_amount_without_discount * \
                            (Decimal("100")-discount.amount)/Decimal("100")
                    else:
                        searched_order.total_amount_discounted = searched_order.total_amount_without_discount - discount.amount

                    searched_order.total_amount_discounted = max(
                        Decimal("0"), searched_order.total_amount_discounted)
                    await db.flush()

                    new_value.update({column.key: getattr(
                        searched_order, column.key) for column in inspect(Order).mapper.column_attrs})

        else:
            old_value.update({column.key: getattr(searched_order, column.key)
                             for column in inspect(Order).mapper.column_attrs})

            searched_order.total_amount_discounted = searched_order.total_amount_without_discount
            await db.flush()

            new_value.update({column.key: getattr(searched_order, column.key)
                             for column in inspect(Order).mapper.column_attrs})

        result = await db.execute(select(PaymentHistory).where(
            PaymentHistory.order_id == order.order_id).with_for_update())

        payment_history = result.scalar_one_or_none()

        if payment_history:
            payment_history.payment_amount = searched_order.total_amount_discounted

        await db.commit()

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=order.order_id,
            entity_type="order",
            event="ORDER_ITEM(S)_DELETED",
            old_value=old_value,
            new_value=new_value
        )

        return {"Item(s) deleted successfully."}

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        logger.error(f"Delete order items for order {order.order_id} failed")
        await db.rollback()
        raise
