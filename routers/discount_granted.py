from fastapi import APIRouter, Depends
from schemas.discount_granted import GetDiscountGranted, DiscountGrantedFilter
from crud.discount_granted import get_discount_granted
from models.people import Person
from sqlalchemy.ext.asyncio import AsyncSession
import auth
from database.connect import get_db


router = APIRouter(prefix='/discount_granted', tags=["DiscountGranted"])


@router.post('/get_people_by_discount_name', response_model=GetDiscountGranted)
async def read_discount_granted(filter_discount: DiscountGrantedFilter, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_discount_granted(filter_discount, current_user, db)
