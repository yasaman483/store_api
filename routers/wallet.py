from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.wallet import WalletResopnse, UpdateAmount
from crud.wallet import update_wallet_amount, get_remain_wallet_amount
from models.people import Person
from database.connect import get_db
import auth


router = APIRouter(prefix='/Wallet', tags=["wallet"])


@router.post('/update_wallet_amount', response_model=WalletResopnse)
async def add_wallet_amount(added_amount: UpdateAmount, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_wallet_amount(added_amount, current_user, db)


@router.post('/get_remain_wallet_amount')
async def recieve_wallet_amount(current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_remain_wallet_amount(current_user, db)
