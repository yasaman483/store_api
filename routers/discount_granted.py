from fastapi import APIRouter, Depends
from schemas.discount_granted import DiscountGrantedResponse, GetDiscountId
from schemas.discount import DiscountUpdateGet
from crud.discount_granted import get_people_by_discount_name, get_people_by_discount_id
from models.people import Person
from sqlalchemy.ext.asyncio import AsyncSession
import auth
from database.connect import get_db


router = APIRouter(prefix='/discount_granted', tags=["DiscountGranted"])


@router.post('/get_people_by_discount_name', response_model=list[DiscountGrantedResponse])
async def read_people_by_discount_name(discount: DiscountUpdateGet, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_people_by_discount_name(discount, current_user, db)


@router.post('/get_people_by_discount_id', response_model=list[DiscountGrantedResponse])
async def read_people_by_discount_id(discount: GetDiscountId, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_people_by_discount_id(discount, current_user, db)
