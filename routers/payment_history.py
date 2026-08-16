from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from crud.payment_history import get_payment_histories, get_payment_history_by_id
from schemas.payment_history import PaymentHistoryResponse, GetPaymentHistoryId
from models.people import People
import auth


router = APIRouter(prefix='/payment_history', tags=['PaymentHistory'])


@router.post('/payment_histories', response_model=list[PaymentHistoryResponse])
async def read_payment_histories(current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_payment_histories(current_user, db)


@router.post('/payment_history_by_id', response_model=PaymentHistoryResponse)
async def read_payment_history_by_id(payment_history: GetPaymentHistoryId, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_payment_history_by_id(payment_history, current_user, db)
