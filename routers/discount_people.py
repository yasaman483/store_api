from fastapi import APIRouter, Depends
from schemas.discount_people import DiscountPeopleResponse, GetDiscountId
from schemas.discount import DiscountUpdateGet
from crud.discount_people import get_people_by_discount_name, get_people_by_discount_id
from models.people import People
from sqlalchemy.ext.asyncio import AsyncSession
import auth
from database.connect import get_db


router = APIRouter(prefix='/get_discount_people', tags=["GetDiscount"])


@router.post('/get_people_by_discount_name', response_model=list[DiscountPeopleResponse])
async def read_people_by_discount_name(discount: DiscountUpdateGet, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_people_by_discount_name(discount, current_user, db)


@router.post('/get_people_by_discount_id', response_model=list[DiscountPeopleResponse])
async def read_people_by_discount_id(discount: GetDiscountId, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_people_by_discount_id(discount, current_user, db)
