from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from models.people import Person
from schemas.discount import DiscountCreate, DiscountResponse, DiscountUpdateGet, DiscountUpdateSent, GetDiscountId, GetDiscountName
from crud.discount import create_discount, get_discounts, update_discount, delete_discount, get_discount_by_name, get_discount_by_id
import auth

router = APIRouter(prefix='/discount', tags=['discount'])


@router.post('/create_discount', response_model=DiscountResponse)
async def add_discount(discount: DiscountCreate, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await create_discount(discount, current_user, db)


@router.post('/read_discounts', response_model=list[DiscountResponse])
async def read_discounts(current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_discounts(current_user, db)


@router.post('/read_discount_by_name', response_model=DiscountResponse)
async def read_discount_by_name(discount: GetDiscountName, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_discount_by_name(discount, current_user, db)


@router.post('/read_discount_by_id', response_model=DiscountResponse)
async def read_discount_by_id(discount: GetDiscountId, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_discount_by_id(discount, current_user, db)


@router.put('/update_discount', response_model=DiscountResponse)
async def edit_discount(current_discount: DiscountUpdateGet, new_discount: DiscountUpdateSent, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_discount(current_discount, new_discount, current_user, db)


@router.delete('/delete_discount')
async def remove_discount(discount: DiscountUpdateGet, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await delete_discount(discount, current_user, db)
