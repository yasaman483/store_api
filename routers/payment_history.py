from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from crud.payment_history import get_payment_histories
from schemas.payment_history import GetPaymentHistory, FilterPaymentHistory
from models.people import Person
import auth


router = APIRouter(prefix='/payment_history', tags=['PaymentHistory'])


@router.post('/read_payment_histories', response_model=GetPaymentHistory)
async def read_payment_histories(filter_payment_history: FilterPaymentHistory, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_payment_histories(filter_payment_history, current_user, db)
