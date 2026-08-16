from models.people import People
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.discount_people import DiscountPeople
from models.discount import Discount
from fastapi import HTTPException
from schemas.people import Roles
from schemas.discount import DiscountUpdateGet
from schemas.discount_people import GetDiscountId


async def get_people_by_discount_name(discount: DiscountUpdateGet, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        raise HTTPException(
            status_code=403, detail=f"Not authorized to get people who got discounts")

    result = await db.execute(select(Discount).where(
        Discount.discount_name == discount.discount_name))

    searched_discount = result.scalar_one_or_none()

    if searched_discount is None:
        raise HTTPException(
            status_code=404, detail=f"Discount {discount.discount_name} not found")

    result = await db.execute(select(DiscountPeople).where(
        DiscountPeople.discount_id == searched_discount.discount_id))

    people = result.scalars().all()

    return people


async def get_people_by_discount_id(discount: GetDiscountId, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER and current_user.role != Roles.EMPLOYEE:
        raise HTTPException(
            status_code=403, detail=f"Not authorized to get people who got discounts")

    result = await db.execute(select(Discount).where(
        Discount.discount_id == discount.discount_id))

    searched_discount = result.scalar_one_or_none()

    if searched_discount is None:
        raise HTTPException(
            status_code=404, detail=f"Discount {discount.discount_id} not found")

    result = await db.execute(select(DiscountPeople).where(
        DiscountPeople.discount_id == searched_discount.discount_id))

    people = result.scalars().all()

    return people
