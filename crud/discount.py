from fastapi import HTTPException
from schemas.discount import DiscountCreate, DiscountUpdateGet, DiscountUpdateSent, FilterDiscount, GetDiscount
from models.discount import Discount
from models.people import Person
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, asc, desc, func
from sqlalchemy.inspection import inspect
from schemas.people import Roles, PersonStatus
from models.discount_granted import DiscountGranted
from schemas.discount import DiscountStatus
import logging
from crud.audit_log import create_audit_log
from schemas.audit import AuditContext, AuditStatus
from math import ceil
from schemas.wallet import SortOrder
from crud.wallet import make_json_format

logger = logging.getLogger(__name__)


async def create_discount(discount: DiscountCreate, audit: AuditContext, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="dsicount",
            event="DISCOUNT_CREATED",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail='Not authorized for creating discount')
    try:
        new_value = dict()

        new_discount = Discount(
            discount_name=discount.discount_name,
            discount_type=discount.discount_type,
            amount=discount.amount,
            expired_at=discount.expired_at,
            discount_status=discount.discount_status,
            active_for_all=discount.active_for_all
        )

        db.add(new_discount)
        await db.flush()

        new_value = {column.key: getattr(
            new_discount, column.key) for column in inspect(Discount).mapper.column_attrs}

        new_value["people"] = []
        if discount.active_for_all:
            result = await db.execute(select(Person).where(
                Person.role == Roles.CUSTOMER))

            all_people = result.scalars().all()

            if not all_people:
                raise HTTPException(status_code=404, detail="No person found.")

            for i in range(len(all_people)):
                new_discount_people = DiscountGranted(
                    discount_id=new_discount.discount_id,
                    user_id=all_people[i].user_id
                )

                db.add(new_discount_people)
                await db.flush()
                new_value["people"].append(new_discount_people.user_id)

        elif discount.people:
            for i in range(len(discount.people)):
                result = await db.execute(select(Person).where(
                    Person.phone == discount.people[i]))

                user = result.scalar_one_or_none()

                if user is None:
                    raise HTTPException(
                        status_code=404, detail="User not found")

                if user.person_status == PersonStatus.UNACTIVE:
                    raise HTTPException(
                        status_code=400, detail="The user is not active")

                new_discount_people = DiscountGranted(
                    discount_id=new_discount.discount_id,
                    user_id=user.user_id
                )

                db.add(new_discount_people)
                await db.flush()
                new_value["people"].append(new_discount_people.user_id)

        new_value = make_json_format(new_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=new_discount.discount_id,
            entity_type="dsicount",
            event="DISCOUNT_CREATED",
            old_value=None,
            new_value=new_value
        )

        await db.commit()
        await db.refresh(new_discount)

        return new_discount

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        logger.error(f"Create discount {discount.discount_name} failed")
        await db.rollback()
        raise


async def get_discounts(audit: AuditContext, filter_discount: FilterDiscount, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="dsicount",
            event="DISCOUNTS_READ",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail='Not authorized for getting discounts')

    filters = []
    if filter_discount.discount_id is not None:
        filters.append(Discount.discount_id == filter_discount.discount_id)
    if filter_discount.discount_name is not None:
        filters.append(Discount.discount_name == filter_discount.discount_name)
    if filter_discount.discount_type is not None:
        filters.append(Discount.discount_type == filter_discount.discount_type)
    if filter_discount.min_amount is not None:
        filters.append(Discount.amount >= filter_discount.min_amount)
    if filter_discount.max_amount is not None:
        filters.append(Discount.amount <= filter_discount.max_amount)
    if filter_discount.expired_before_at is not None:
        filters.append(Discount.expired_at <=
                       filter_discount.expired_before_at)
    if filter_discount.expired_after_at is not None:
        filters.append(Discount.expired_at >= filter_discount.expired_after_at)
    if filter_discount.active_for_all is not None:
        filters.append(Discount.active_for_all ==
                       filter_discount.active_for_all)
    if filter_discount.discount_status is not None:
        filters.append(Discount.discount_status ==
                       filter_discount.discount_status)

    query = select(Discount).where(*filters)
    result = select(func.count()).select_from(query.subquery())
    total = await db.scalar(result)
    offset = (filter_discount.page - 1) * filter_discount.page_size

    if filter_discount.sort_order == SortOrder.ASC:
        query = query.order_by(asc(filter_discount.sort_by)).offset(
            offset).limit(filter_discount.page_size)

    if filter_discount.sort_order == SortOrder.DES:
        query = query.order_by(desc(filter_discount.sort_by)).offset(
            offset).limit(filter_discount.page_size)

    result = await db.execute(query)
    discounts = result.scalars().all()

    if not discounts:
        raise HTTPException(
            status_code=404, detail="There isn't any discount yet")

    return GetDiscount(discounts=discounts, page=filter_discount.page, page_size=filter_discount.page_size, total=total, pages=ceil(total/filter_discount.page_size))


async def update_discount(current_discount: DiscountUpdateGet, new_discount: DiscountUpdateSent, audit: AuditContext, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="dsicount",
            event="DISCOUNT_UPDATE",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail='Not authorized for updating discount')
    try:
        new_value = dict()
        old_value = dict()
        new_value["people"] = []
        old_value["people"] = []
        result = await db.execute(select(Discount).where(
            Discount.discount_name == current_discount.discount_name))

        discount = result.scalar_one_or_none()

        if discount is None:
            raise HTTPException(
                status_code=404, detail=f'Discount {current_discount.discount_name} not found.')

        update_data = new_discount.model_dump(exclude_unset=True)

        if "people" in update_data.keys():
            people = update_data.pop("people")

            for i in range(len(people)):
                result = await db.execute(select(Person).where(
                    Person.user_id == people[i]["user_id"]))

                user = result.scalar_one_or_none()

                if user is None:
                    raise HTTPException(
                        status_code=404, detail=f'Person with phone {people[i]["user_id"]} not found.')

                result = await db.execute(select(DiscountGranted).where(
                    DiscountGranted.user_id == user.user_id, DiscountGranted.discount_id == discount.discount_id))

                discount_person = result.scalar_one_or_none()

                if people[i]["status"] == DiscountStatus.ACTIVE:
                    if discount_person is None:
                        new_discount_people = DiscountGranted(
                            discount_id=discount.discount_id,
                            user_id=user.user_id
                        )

                        db.add(new_discount_people)
                        await db.flush()
                        new_value["people"].append(new_discount_people.user_id)

                else:
                    if discount_person is None:
                        raise HTTPException(
                            status_code=404, detail=f'specified discount {current_discount.discount_name} not found for person with user_id {user.user_id}')

                    await db.delete(discount_person)
                    old_value["people"].append(discount_person.user_id)

        old_value.update({column.key: getattr(discount, column.key)
                         for column in inspect(Discount).mapper.column_attrs})

        for key, value in update_data.items():
            setattr(discount, key, value)
            new_value[key] = value

        new_value = make_json_format(new_value)
        old_value = make_json_format(old_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=discount.discount_id,
            entity_type="dsicount",
            event="DISCOUNT_UPDATE",
            old_value=old_value,
            new_value=new_value
        )

        await db.commit()
        await db.refresh(discount)
        return discount

    except Exception:
        logger.error(f"Update discount {discount.discount_id} failed")
        await db.rollback()
        raise


async def unactive_discount(discount: DiscountUpdateGet, audit: AuditContext, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="dsicount",
            event="DISCOUNT_UNACTIVATED",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail='Not authorized for deleting discount')

    try:
        result = await db.execute(select(Discount).where(
            Discount.discount_name == discount.discount_name))

        searched_discount = result.scalar_one_or_none()

        if searched_discount is None:
            raise HTTPException(
                status_code=404, detail=f'Discount {discount.discount_name} not found.')

        searched_discount.discount_status = DiscountStatus.UNACTIVE

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=searched_discount.discount_id,
            entity_type="dsicount",
            event="DISCOUNT_UNACTIVATED",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        return {f'{searched_discount.discount_name} unactivate successfully'}

    except HTTPException:
        await db.rollback()

    except Exception:
        logger.error(f"Unactive discount {discount.discount_name} failed")
        await db.rollback()
        raise
