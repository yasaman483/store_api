from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import asc, desc, select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from fastapi import HTTPException
from schemas.audit import AuditContext
from schemas.caret_items import FilterCaretItems, GetCaretItems, RemoveCaretItems, CaretItemStatus, CaretItemUpdateStatus, InfoCaretItems
from models.caret_items import CaretItems
from models.people import Person
from models.caret import Caret
from crud.audit_log import create_audit_log
from models.products import Product
from schemas.people import Roles, PersonStatus
from schemas.wallet import SortOrder
from crud.wallet import make_json_format
import logging
from crud.orders import create_order
from schemas.order_items import OrderItemsCreate
from schemas.orders import OrderCreate
from math import ceil

logger = logging.getLogger(__name__)


async def create_caret_items(audit: AuditContext, items: InfoCaretItems, current_user: Person, db: AsyncSession):
    try:
        if current_user.role == Roles.CUSTOMER:
            result = await db.execute(select(Caret).where(Caret.user_id == current_user.user_id))
            caret = result.scalar_one_or_none()
            caret_user_id = current_user.user_id
        elif current_user.role == Roles.MANAGER or current_user.role == Roles.EMPLOYEE:
            result = await db.execute(select(Caret).where(Caret.user_id == items.user_id))
            caret = result.scalar_one_or_none()
            caret_user_id = items.user_id

        if caret is None:
            raise HTTPException(
                status_code=404, detail=f"Caret not found for user {current_user.user_id}")

        products = []
        new_caret_items = dict()
        new_value = []
        for item in items:
            result = await db.execute(select(Product).where(Product.product_id == item.product_id).with_for_update())
            product = result.scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=404, detail=f"Product {item.product_id} not found")

            if product.remain_in_stock < item.quantity:
                raise HTTPException(
                    status_code=400, detail=f"Product {product.product_id} doesn't have enough amount")

            if product.product_id not in products:
                new_caret_item = CaretItems(
                    caret_id=caret.caret_id,
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=product.unit_price
                )
                db.add(new_caret_item)
                await db.flush()
                await db.refresh(new_caret_item)
                new_caret_items[f"{item.product_id}"] = new_caret_item
                products.append(product.product_id)

            else:
                for product_id, caret_item in new_caret_items.items():
                    if int(product_id) == item.product_id:
                        caret_item.quantity += item.quantity
                        break

        await db.flush()

        for caret_item in new_caret_items.values():
            value = {}
            for column in inspect(CaretItems).mapper.column_attrs:
                value[column.key] = getattr(caret_item, column.key)
            new_value.append(value)

        for i in range(len(new_value)):
            new_value[i] = make_json_format(new_value[i])

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=caret_user_id,
            entity_id=None,
            entity_type="caret_items",
            event="CARET_ITEMS_CREATED",
            old_value=None,
            new_value=new_value
        )
        await db.commit()

        return new_value

    except HTTPException:
        await db.rollback()
        raise

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Confiliction happend")

    except Exception:
        logger.exception(
            f"create caret items for user {caret_user_id} failed")
        await db.rollback()
        raise


async def get_caret_items(filter_caret: FilterCaretItems, current_user: Person, db: AsyncSession):
    filters = []
    if current_user.role == Roles.CUSTOMER:
        result = await db.execute(select(Caret).where(Caret.user_id == current_user.user_id))
        user_caret = result.scalar_one_or_none()
        if user_caret is None:
            raise HTTPException(
                status_code=404, detail=f"Caret not found for user {current_user.user_id}")
        filters.append(CaretItems.caret_id == user_caret.caret_id)

    elif filter_caret.caret_id is not None:
        if current_user.role == Roles.MANAGER or current_user.role == Roles.EMPLOYEE:
            filters.append(CaretItems.caret_id == current_user.user_id)

    if filter_caret.product_id is not None:
        filters.append(CaretItems.product_id == filter_caret.product_id)

    if filter_caret.min_quantity is not None:
        filters.append(CaretItems.quantity >= filter_caret.min_quantity)

    if filter_caret.max_quantity is not None:
        filters.append(CaretItems.quantity <= filter_caret.max_quantity)

    if filter_caret.min_unit_price is not None:
        filters.append(CaretItems.unit_price >= filter_caret.min_unit_price)

    if filter_caret.max_unit_price is not None:
        filters.append(CaretItems.unit_price <= filter_caret.max_unit_price)

    if filter_caret.caret_item_status is not None:
        filters.append(CaretItems.caret_item_status ==
                       filter_caret.caret_item_status)

    if filter_caret.before_date_ is not None:
        filters.append(CaretItems.date_ <= filter_caret.before_date_)

    if filter_caret.after_date_ is not None:
        filters.append(CaretItems.date_ >= filter_caret.after_date_)

    query = select(CaretItems).where(*filters)
    result = select(func.count()).select_from(query.subquery())
    offset = (filter_caret.page-1)*filter_caret.page_size
    total = await db.scalar(result)

    if filter_caret.sort_order == SortOrder.ASC:
        query = query.order_by(asc(filter_caret.sort_by)).offset(
            offset).limit(filter_caret.page_size)

    elif filter_caret.sort_order == SortOrder.DES:
        query = query.order_by(desc(filter_caret.sort_by)).offset(
            offset).limit(filter_caret.page_size)

    result = await db.execute(query)
    items = result.scalars().all()

    return GetCaretItems(items=items, page=filter_caret.page, page_size=filter_caret.page_size, total=total, pages=ceil(total/filter_caret.page_size))


async def update_caret_items(items: InfoCaretItems, audit: AuditContext, current_user: Person, db: AsyncSession):
    try:
        if current_user.role == Roles.CUSTOMER:
            user_id = current_user.user_id
            result = await db.execute(select(Caret).where(Caret.user_id == current_user.user_id))
            caret = result.scalar_one_or_none()
        elif current_user.role == Roles.EMPLOYEE or current_user.role == Roles.MANAGER:
            user_id = items.user_id
            result = await db.execute(select(Caret).where(Caret.user_id == items.user_id))
            caret = result.scalar_one_or_none()

        if caret is None:
            raise HTTPException(
                status_code=404, detail=f"Caret not found for user {user_id}")

        result = await db.execute(select(Person).where(Person.user_id == caret.user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=403, detail="User not found")

        if user.person_status == PersonStatus.UNACTIVE:
            raise HTTPException(
                status_code=403, detail="User is not activated")

        products = dict()
        for i in range(len(items.items)):
            if products and items.items[i].product_id in products.keys():
                products[items.items[i].product_id].append(i)
            elif items.items[i].product_id not in products.keys():
                products[items.items[i].product_id] = [i]

        for product in products.values():
            if len(product) > 1:
                for i in range(1, len(product)):
                    items[i] = "None"

        for item in items.items:
            if item == "None":
                items.items.remove(item)

        old_value = dict()
        new_value = dict()
        for item in items.items:
            result = await db.execute(select(CaretItems).where(CaretItems.caret_id == caret.caret_id, CaretItems.product_id == item.product_id))
            caret_item = result.scalar_one_or_none()

            if caret_item is None:
                raise HTTPException(
                    status_code=404, detail=f"Caret item not fount for user {user_id}")

            if caret_item.caret_item_status == CaretItemStatus.CHECKED:
                raise HTTPException(
                    status_code=400, detail=f"Item {item.product_id} has been already checked.")

            result = await db.execute(select(Product).where(Product.product_id == item.product_id))
            product = result.scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=404, detail=f"Product {item.product_id} not found")

            if product.remain_in_stock < item.quantity:
                raise HTTPException(
                    status_code=400, detail=f"Product {product.product_id} doesn't have enough amount")

            old_value.update({column.key: getattr(caret_item, column.key)
                             for column in inspect(CaretItems).mapper.column_attrs})

            caret_item.quantity = item.quantity
            await db.flush()
            await db.refresh(caret_item)

            new_value.update({column.key: getattr(caret_item, column.key)
                             for column in inspect(CaretItems).mapper.column_attrs})

            new_value = make_json_format(new_value)
            old_value = make_json_format(old_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=user_id,
            entity_id=None,
            entity_type="caret_item",
            event="CARET_ITEM_UPDATED",
            old_value=old_value,
            new_value=new_value
        )
        await db.commit()

        result = await db.execute(select(CaretItems).where(CaretItems.caret_id == caret.caret_id))
        caret_items = result.scalars().all()

        return caret_items

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        logger.exception(
            f"update caret items for user {user_id} failed")

        await db.rollback()
        raise


async def update_caret_items_status(items: CaretItemUpdateStatus, audit: AuditContext, current_user: Person, db: AsyncSession):
    try:
        old_value = dict()
        new_value = dict()

        if current_user.role == Roles.CUSTOMER:
            user_id = current_user.user_id
            result = await db.execute(select(Caret).where(Caret.user_id == user_id))
            caret = result.scalar_one_or_none()
            result = await db.execute(select(Person).where(Person.user_id == current_user.user_id))
            caret_person = result.scalar_one_or_none()

        elif current_user.role == Roles.MANAGER or current_user.role == Roles.EMPLOYEE:
            result = await db.execute(select(Caret).where(Caret.caret_id == items.caret_id))
            caret = result.scalar_one_or_none()
            user_id = caret.user_id
            result = await db.execute(select(Person).where(Person.user_id == caret.user_id))
            caret_person = result.scalar_one_or_none()

        if caret is None:
            raise HTTPException(
                status_code=404, detail=f"Caret not found for user {user_id}")

        result = await db.execute(select(Person).where(Person.user_id == caret.user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=403, detail="User not found")

        if user.person_status == PersonStatus.UNACTIVE:
            raise HTTPException(
                status_code=403, detail="User is not activated")

        orders = []
        for item in items.items:
            result = await db.execute(select(CaretItems).where(CaretItems.caret_id == caret.caret_id, CaretItems.product_id == item.product_id))
            caret_item = result.scalar_one_or_none()

            if caret_item is None:
                raise HTTPException(
                    status_code=404, detail=f"Caret item not fount for user {user_id}")

            if caret_item.caret_item_status == CaretItemStatus.CHECKED:
                raise HTTPException(
                    status_code=400, detail=f"Iitem {item.product_id} has been already checked")

            result = await db.execute(select(Product).where(Product.product_id == item.product_id))
            product = result.scalar_one_or_none()

            if product is None:
                raise HTTPException(
                    status_code=404, detail=f"product {item.product_id} not found")

            old_value.update({column.key: getattr(caret_item, column.key)
                              for column in inspect(CaretItems).mapper.column_attrs})

            caret_item.caret_item_status = CaretItemStatus.CHECKED

            await db.flush()
            await db.refresh(caret_item)

            new_value.update({column.key: getattr(caret_item, column.key)
                              for column in inspect(CaretItems).mapper.column_attrs})

            new_value = make_json_format(new_value)
            old_value = make_json_format(old_value)

            orders.append(OrderItemsCreate(
                quantity=caret_item.quantity, product_name=product.product_name))

        response = await create_order(OrderCreate(items=orders, payment_method=items.payment_method, discount=items.discount), audit, caret_person, db)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="caret_item",
            event="CARET_ITEM_STATUS_UPDATED",
            old_value=old_value,
            new_value=new_value
        )
        await db.commit()

        return response

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()

        logger.exception(
            f"update caret items for user {user_id} failed")
        raise


async def delete_caret_items(items: RemoveCaretItems, audit: AuditContext, current_user: Person, db: AsyncSession):
    try:
        if current_user.role == Roles.CUSTOMER:
            user_id = current_user.user_id
            result = await db.execute(select(Caret).where(Caret.user_id == current_user.user_id))
            caret = result.scalar_one_or_none()

            if caret is None:
                raise HTTPException(
                    status_code=404, detail=f"Caret not found for user {current_user.user_id}")

            result = await db.execute(select(Person).where(Person.user_id == caret.user_id))
            user = result.scalar_one_or_none()

            if user is None:
                raise HTTPException(status_code=403, detail="User not found")

            if user.person_status == PersonStatus.UNACTIVE:
                raise HTTPException(
                    status_code=403, detail="User is not activated")

            old_value = dict()
            new_value = dict()
            for item in items.products:
                result = await db.execute(select(CaretItems).where(CaretItems.caret_id == caret.caret_id, CaretItems.product_id == item.product_id))
                caret_item = result.scalar_one_or_none()

                if caret_item is None:
                    raise HTTPException(
                        status_code=404, detail=f"Caret item not fount for user {current_user.user_id}")

                if caret_item.caret_item_status == CaretItemStatus.CHECKED:
                    raise HTTPException(
                        status_code=400, detail=f'Can not change the item {item.product_id} status anymore')

                old_value.update({column.key: getattr(caret_item, column.key)
                                  for column in inspect(CaretItems).mapper.column_attrs})
                caret_item.caret_item_status = CaretItemStatus.DELETED
                await db.flush()
                new_value.update({column.key: getattr(caret_item, column.key)
                                  for column in inspect(CaretItems).mapper.column_attrs})

        elif current_user.role == Roles.MANAGER or current_user.role == Roles.EMPLOYEE:
            old_value = dict()
            new_value = dict()

            result = await db.execute(select(Caret).where(Caret.caret_id == items.caret_id))
            caret = result.scalar_one_or_none()

            if caret is None:
                raise HTTPException(
                    status_code=404, detail=f"Caret not found for user {current_user.user_id}")

            user_id = caret.user_id

            for item in items.products:
                result = await db.execute(select(CaretItems).where(CaretItems.caret_id == caret.caret_id, CaretItems.product_id == item.product_id))
                caret_item = result.scalar_one_or_none()

                if caret_item is None:
                    raise HTTPException(
                        status_code=404, detail=f"Caret item not fount for user {current_user.user_id}")

                if caret_item.caret_item_status == CaretItemStatus.CHECKED:
                    raise HTTPException(
                        status_code=400, detail=f'Can not change the item {item.product_id} status anymore')

                old_value.update({column.key: getattr(caret_item, column.key)
                                  for column in inspect(CaretItems).mapper.column_attrs})
                caret_item.caret_item_status = CaretItemStatus.DELETED
                await db.flush()
                new_value.update({column.key: getattr(caret_item, column.key)
                                  for column in inspect(CaretItems).mapper.column_attrs})

        new_value = make_json_format(new_value)
        old_value = make_json_format(old_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="caret_item",
            event="CARET_ITEM_UPDATED",
            old_value=old_value,
            new_value=new_value
        )
        await db.commit()

        result = await db.execute(select(CaretItems).where(CaretItems.caret_id == caret.caret_id))
        caret_items = result.scalars().all()

        if caret_items is not None:
            return caret_items
        else:
            return {"The caret is empty"}

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        await db.rollback()

        logger.exception(
            f"update caret items for user {user_id} failed")
        raise
