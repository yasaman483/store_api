from fastapi import HTTPException
from schemas.discount import DiscountCreate, DiscountUpdateGet, DiscountUpdateSent, GetDiscountId, GetDiscountName
from models.discount import Discount
from models.people import Person
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from schemas.people import Roles
from models.discount_granted import DiscountGranted
from schemas.discount_granted import DiscountStatus
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)


async def create_discount(discount: DiscountCreate, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        end_time = datetime.now(UTC)
        error = {
            "event": "Create discount failed",
            "method": "POST",
            "error": "Not authorized to create discount",
            "path": "/discount/create_discount",
            "user_id": current_user.user_id,
            "status_code": 403,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        raise HTTPException(
            status_code=403, detail='Not authorized for creating discount')
    try:
        new_discount = Discount(
            discount_name=discount.discount_name,
            discount_type=discount.discount_type,
            amount=discount.amount,
            expired_at=discount.expired_at,
            active_for_all=discount.active_for_all
        )

        db.add(new_discount)
        await db.flush()

        if discount.active_for_all:
            result = await db.execute(select(Person).where(
                Person.role == Roles.CUSTOMER))

            all_people = result.scalars().all()

            for i in range(len(all_people)):
                new_discount_people = DiscountGranted(
                    discount_id=new_discount.discount_id,
                    people_id=all_people[i].user_id
                )

                db.add(new_discount_people)
                await db.flush()

        elif discount.people:
            for i in range(len(discount.people)):
                result = await db.execute(select(Person).where(
                    Person.phone == discount.people[i]))

                user = result.scalar_one_or_none()

                new_discount_people = DiscountGranted(
                    discount_id=new_discount.discount_id,
                    people_id=user.user_id
                )

                db.add(new_discount_people)
                await db.flush()

        await db.commit()
        await db.refresh(new_discount)

        end_time = datetime.now(UTC)
        info = {
            "event": "Create discount succeeded",
            "method": "POST",
            "path": "/discount/create_discount",
            "user_id": current_user.user_id,
            "discount_id": new_discount.discount_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return new_discount

    except Exception as ex:
        end_time = datetime.now(UTC)
        error = {
            "event": "Create discount failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/discount/create_discount",
            "user_id": current_user.user_id,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        await db.rollback()
        raise ex


async def get_discounts(current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        end_time = datetime.now(UTC)
        error = {
            "event": "Get discounts failed",
            "method": "POST",
            "error": "Not authorized to get discounts",
            "path": "/discount/read_discounts",
            "user_id": current_user.user_id,
            "status_code": 403,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        raise HTTPException(
            status_code=403, detail='Not authorized for getting discounts')

    result = await db.execute(select(Discount))

    discounts = result.scalars().all()

    if not discounts:
        raise HTTPException(
            status_code=404, detail='There are not any discounts yet')

    end_time = datetime.now(UTC)
    info = {
        "event": "Get discounts succeeded",
        "method": "POST",
        "path": "/discount/read_discounts",
        "user_id": current_user.user_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return discounts


async def get_discount_by_name(discount: GetDiscountName, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        end_time = datetime.now(UTC)
        error = {
            "event": "Get discount by name failed",
            "method": "POST",
            "error": "Not authorized to get discount by name",
            "path": "/discount/read_discount_by_name",
            "user_id": current_user.user_id,
            "status_code": 403,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        raise HTTPException(
            status_code=403, detail='Not authorized for getting discount by name')

    result = await db.execute(select(Discount).where(Discount.discount_name == discount.discount_name))

    searched_discount = result.scalar_one_or_none()

    if searched_discount is None:
        raise HTTPException(
            status_code=403, detail='There are not any discounts yet')

    end_time = datetime.now(UTC)
    info = {
        "event": "Get discount by name succeeded",
        "method": "POST",
        "path": "/discount/read_discount_by_name",
        "user_id": current_user.user_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return searched_discount


async def get_discount_by_id(discount: GetDiscountId, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        end_time = datetime.now(UTC)
        error = {
            "event": "Get discount by id failed",
            "method": "POST",
            "error": "Not authorized to get discount by id",
            "path": "/discount/read_discount_by_id",
            "user_id": current_user.user_id,
            "status_code": 403,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        raise HTTPException(
            status_code=403, detail='Not authorized for getting discount by id')

    result = await db.execute(select(Discount).where(Discount.discount_id == discount.discount_id))

    searched_discount = result.scalar_one_or_none()

    if searched_discount is None:
        raise HTTPException(
            status_code=403, detail=f'Discount {discount.discount_id} not found')

    end_time = datetime.now(UTC)
    info = {
        "event": "Get discount by id succeeded",
        "method": "POST",
        "path": "/discount/read_discount_by_id",
        "user_id": current_user.user_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return searched_discount


async def update_discount(current_discount: DiscountUpdateGet, new_discount: DiscountUpdateSent, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        end_time = datetime.now(UTC)
        error = {
            "event": "Update discount failed",
            "method": "POST",
            "error": "Not authorized to update discount",
            "path": "/discount/update_discount",
            "user_id": current_user.user_id,
            "discount_name": current_discount.discount_name,
            "status_code": 403,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        raise HTTPException(
            status_code=403, detail='Not authorized for updating discount')
    try:
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
                    Person.phone == people[i]["phone"]))

                user = result.scalar_one_or_none()

                if user is None:
                    raise HTTPException(
                        status_code=404, detail=f'Person with phone {people[i]["phone"]} not found.')

                result = await db.execute(select(DiscountGranted).where(
                    DiscountGranted.people_id == user.user_id, DiscountGranted.discount_id == discount.discount_id))

                discount_person = result.scalar_one_or_none()

                if people[i]["status"] == DiscountStatus.ACTIVE:
                    if discount_person is None:
                        new_discount_people = DiscountGranted(
                            discount_id=discount.discount_id,
                            people_id=user.user_id
                        )

                        db.add(new_discount_people)
                        await db.flush()

                else:
                    if discount_person is None:
                        raise HTTPException(
                            status_code=404, detail=f'specified discount {current_discount.discount_name} not found for person with {user.phone} phone number')

                    await db.delete(discount_person)

        for key, value in update_data.items():
            setattr(discount, key, value)

        end_time = datetime.now(UTC)
        info = {
            "event": "Update discount succeeded",
            "method": "POST",
            "path": "/discount/update_discount",
            "user_id": current_user.user_id,
            "discount_id": discount.discount_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        await db.commit()
        await db.refresh(discount)
        return discount

    except Exception as ex:
        end_time = datetime.now(UTC)
        error = {
            "event": "Update discount failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/discount/update_discount",
            "user_id": current_user.user_id,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        await db.rollback()
        raise ex


async def delete_discount(discount: DiscountUpdateGet, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        end_time = datetime.now(UTC)
        error = {
            "event": "Delete discount failed",
            "method": "POST",
            "error": "Not authorized to delete discount",
            "path": "/discount/delete_discount",
            "user_id": current_user.user_id,
            "discount_name": discount.discount_name,
            "status_code": 403,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        raise HTTPException(
            status_code=403, detail='Not authorized for deleting discount')
    try:
        result = await db.execute(select(Discount).where(
            Discount.discount_name == discount.discount_name))

        searched_discount = result.scalar_one_or_none()

        if searched_discount is None:
            raise HTTPException(
                status_code=404, detail=f'Discount {discount.discount_name} not found.')

        await db.delete(searched_discount)
        await db.commit()

        end_time = datetime.now(UTC)
        info = {
            "event": "Delete discount succeeded",
            "method": "POST",
            "path": "/discount/delete_discount",
            "user_id": current_user.user_id,
            "discount_name": discount.discount_name,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return {f'{searched_discount.discount_name} deleted successfully'}

    except Exception as ex:
        end_time = datetime.now(UTC)
        error = {
            "event": "Delete discount failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/discount/delete_discount",
            "user_id": current_user.user_id,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        await db.rollback()
        raise ex
