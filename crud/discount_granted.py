from models.people import Person
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.discount_granted import DiscountGranted
from models.discount import Discount
from fastapi import HTTPException
from schemas.people import Roles
from schemas.discount import DiscountUpdateGet
from schemas.discount_granted import GetDiscountId
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)


async def get_people_by_discount_name(discount: DiscountUpdateGet, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        end_time = datetime.now(UTC)
        error = {
            "event": "Get granted discounts by discount name failed",
            "method": "POST",
            "error": "Not authorized to get people using discount name",
            "path": "/discount_granted/get_people_by_discount_name",
            "user_id": current_user.user_id,
            "discount_name": discount.discount_name,
            "status_code": 403,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        raise HTTPException(
            status_code=403, detail=f"Not authorized to get people who got discounts")

    result = await db.execute(select(Discount).where(
        Discount.discount_name == discount.discount_name))

    searched_discount = result.scalar_one_or_none()

    if searched_discount is None:
        raise HTTPException(
            status_code=404, detail=f"Discount {discount.discount_name} not found")

    result = await db.execute(select(DiscountGranted).where(
        DiscountGranted.discount_id == searched_discount.discount_id))

    people = result.scalars().all()

    end_time = datetime.now(UTC)
    info = {
        "event": "Get granted discounts by discount name succeeded",
        "method": "POST",
        "path": "/discount_granted/get_people_by_discount_name",
        "user_id": current_user.user_id,
        "discount_name": discount.discount_name,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return people


async def get_people_by_discount_id(discount: GetDiscountId, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        end_time = datetime.now(UTC)
        error = {
            "event": "Get granted discounts by discount id failed",
            "method": "POST",
            "error": "Not authorized to get people using discount id",
            "path": "/discount_granted/get_people_by_discount_id",
            "user_id": current_user.user_id,
            "discount_id": discount.discount_id,
            "status_code": 403,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        raise HTTPException(
            status_code=403, detail=f"Not authorized to get people who got discounts")

    result = await db.execute(select(Discount).where(
        Discount.discount_id == discount.discount_id))

    searched_discount = result.scalar_one_or_none()

    if searched_discount is None:
        raise HTTPException(
            status_code=404, detail=f"Discount {discount.discount_id} not found")

    result = await db.execute(select(DiscountGranted).where(
        DiscountGranted.discount_id == searched_discount.discount_id))

    people = result.scalars().all()

    end_time = datetime.now(UTC)
    info = {
        "event": "Get granted discounts by discount id succeeded",
        "method": "POST",
        "path": "/discount_granted/get_people_by_discount_id",
        "user_id": current_user.user_id,
        "discount_id": discount.discount_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return people
