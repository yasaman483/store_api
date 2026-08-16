from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from models.people import People
from models.order_items import OrderItems
from models.orders import Orders
from schemas.order_items import OrderItemsUpdate, OrderItemsDelete
from schemas.orders import OrderStatus, OrderUpdateById
from models.products import Products
from models.discount import Discount
from models.discount_people import DiscountPeople
from schemas.discount import DiscountType
from decimal import Decimal
from models.payment_history import PaymentHistory


async def get_order_items(order: OrderUpdateById, current_user: People, db: AsyncSession):
    result = await db.execute(select(OrderItems).where(
        OrderItems.order_id == order.order_id))

    order_items = result.scalars().all()

    if not order_items:
        raise HTTPException(
            status_code=404, detail=f"Order {order.order_id} not found")

    result = await db.execute(select(Orders).where(
        Orders.order_id == order.order_id))

    searched_order = result.scalar_one_or_none()

    if searched_order.customer_id != current_user.people_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to get this order")

    return order_items


async def update_order_item(order: OrderUpdateById, order_items: list[OrderItemsUpdate], current_user: People, db: AsyncSession):
    try:
        result = await db.execute(select(Orders).where(
            Orders.order_id == order.order_id))

        searched_order = result.scalar_one_or_none()

        if not searched_order:
            raise HTTPException(status_code=404, detail='No order item found')

        if searched_order.customer_id != current_user.people_id:
            raise HTTPException(
                status_code=403, detail="Not authorized to  update the order")

        if searched_order.order_status != OrderStatus.UNCONFIRMED:
            raise HTTPException(
                status_code=400, detail='Not allowed to update the order anymore')

        updated_list = []
        total_amount = 0
        for i in range(len(order_items)):
            result = await db.execute(select(Products).where(
                Products.product_name == order_items[i].product_name))

            product = result.scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=404, detail='Product not found')

            result = await db.execute(select(OrderItems).where(
                OrderItems.order_id == order.order_id, OrderItems.product_id == product.product_id))

            searched_order_item = result.scalar_one_or_none()

            if searched_order_item is None:
                if product.remain_in_stock < order_items[i].quantity:
                    raise HTTPException(
                        status_code=400, detail=f"Product {product.product_name} doesn't have enough amount.")

                new_order_item = OrderItems(
                    order_id=order.order_id,
                    product_id=product.product_id,
                    quantity=order_items[i].quantity,
                    unit_price=product.unit_price
                )

                product.remain_in_stock -= order_items[i].quantity
                total_amount += order_items[i].quantity*product.unit_price

                db.add(new_order_item)
                await db.flush()
                await db.refresh(new_order_item)
                updated_list.append(new_order_item)
                continue

            if (order_items[i].quantity-searched_order_item.quantity) > product.remain_in_stock:
                raise HTTPException(
                    status_code=400, detail=f"Product {product.product_name} doesn't have enough amount.")

            if order_items[i].quantity > searched_order_item.quantity:
                product.remain_in_stock -= order_items[i].quantity - \
                    searched_order_item.quantity

                total_amount += (order_items[i].quantity -
                                 searched_order_item.quantity)*product.unit_price

            if order_items[i].quantity < searched_order_item.quantity:
                product.remain_in_stock += searched_order_item.quantity - \
                    order_items[i].quantity

                total_amount += (order_items[i].quantity -
                                 searched_order_item.quantity)*product.unit_price

            searched_order_item.quantity = order_items[i].quantity

            updated_list.append(searched_order_item)
            await db.flush()
            await db.refresh(searched_order_item)

        searched_order.total_amount_without_discount += total_amount

        if searched_order.discount:
            result = await db.execute(select(Discount).where(
                Discount.discount_name == searched_order.discount))

            discount = result.scalar_one_or_none()

            if discount:
                result = await db.execute(select(DiscountPeople).where(DiscountPeople.discount_id ==
                                                                       discount.discount_id, DiscountPeople.order_id == order.order_id))

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

        result = await db.execute(select(PaymentHistory).where(
            PaymentHistory.order_id == order.order_id))

        payment_history = result.scalar_one_or_none()

        if payment_history:
            payment_history.payment_amount = searched_order.total_amount_discounted

        await db.commit()
        return updated_list

    except Exception as ex:
        await db.rollback()
        raise ex


async def delete_order_item(order: OrderUpdateById, order_items: list[OrderItemsDelete], current_user: People, db: AsyncSession):
    result = await db.execute(select(Orders).where(
        Orders.order_id == order.order_id))

    searched_order = result.scalar_one_or_none()

    if not searched_order:
        raise HTTPException(status_code=404, detail='No order item found')

    if searched_order.customer_id != current_user.people_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to  update the order")

    if searched_order.order_status != OrderStatus.UNCONFIRMED:
        raise HTTPException(
            status_code=400, detail='Not allowed to delete the order anymore')

    for i in range(len(order_items)):
        result = await db.execute(select(Products).where(
            Products.product_name == order_items[i].product_name))

        product = result.scalar_one_or_none()

        if product is None:
            raise HTTPException(status_code=404, detail='Product not found')

        result = await db.execute(select(OrderItems).where(
            OrderItems.order_id == order.order_id, OrderItems.product_id == product.product_id))

        searched_order_item = result.scalar_one_or_none()

        if searched_order_item is None:
            raise HTTPException(status_code=404, detail='Order item not found')

        product.remain_in_stock += searched_order_item.quantity
        searched_order.total_amount_without_discount -= searched_order_item.quantity * \
            searched_order_item.unit_price

        await db.delete(searched_order_item)

    await db.flush()

    result = await db.execute(select(func.count()).select_from(OrderItems).where(
        OrderItems.order_id == order.order_id))

    remaining_items = result.scalar_one()

    if remaining_items == 0:
        await db.delete(order)
        if searched_order.discount:
            result = await db.execute(select(Discount).where(
                Discount.discount_name == searched_order.discount))

            user_discount = result.scalar_one_or_none()

            if user_discount:
                result = await db.execute(select(DiscountPeople).where(DiscountPeople.discount_id ==
                                                                       user_discount.discount_id, DiscountPeople.order_id == order.order_id))
                person_discount = result.scalar_one_or_none()

                if person_discount:
                    person_discount.used = False
                    person_discount.used_at = None

    elif searched_order.discount:
        result = await db.execute(select(Discount).where(
            Discount.discount_name == searched_order.discount))

        discount = result.scalar_one_or_none()

        if discount:
            result = await db.execute(select(DiscountPeople).where(DiscountPeople.discount_id ==
                                                                   discount.discount_id, DiscountPeople.order_id == order.order_id))
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

    result = await db.execute(select(PaymentHistory).where(
        PaymentHistory.order_id == order.order_id))

    payment_history = result.scalar_one_or_none()

    if payment_history:
        payment_history.payment_amount = searched_order.total_amount_discounted

    await db.commit()

    return {"Item(s) deleted successfully."}
