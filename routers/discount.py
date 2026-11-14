from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from models.people import Person
from schemas.discount import DiscountCreate, DiscountResponse, DiscountUpdateGet, DiscountUpdateSent, GetDiscount, FilterDiscount
from crud.discount import create_discount, get_discounts, update_discount, unactive_discount
import auth
from crud.audit_log import create_audit_context

router = APIRouter(prefix='/discount', tags=['discount'])


@router.post('/create_discount', response_model=DiscountResponse)
async def add_discount(discount: DiscountCreate, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await create_discount(discount, audit, current_user, db)


@router.post('/read_discounts', response_model=GetDiscount)
async def read_discounts(request: Request, filter_discount: FilterDiscount, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await get_discounts(audit, filter_discount, current_user, db)


@router.patch('/update_discount', response_model=DiscountResponse)
async def edit_discount(current_discount: DiscountUpdateGet, new_discount: DiscountUpdateSent, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await update_discount(current_discount, new_discount, audit, current_user, db)


@router.delete('/delete_discount')
async def remove_discount(discount: DiscountUpdateGet, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await unactive_discount(discount, audit, current_user, db)
