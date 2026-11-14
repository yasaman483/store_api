from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.wallet import WalletResponse, UpdateWalletAmount, FilterWallets, GetWallets
from crud.wallet import update_wallet_amount, get_remain_wallet_amount
from models.people import Person
from database.connect import get_db
import auth
from crud.audit_log import create_audit_context


router = APIRouter(prefix='/wallet', tags=["wallet"])


@router.patch('/update_wallet_amount', response_model=WalletResponse)
async def add_wallet_amount(added_amount: UpdateWalletAmount, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await update_wallet_amount(added_amount, audit, current_user, db)


@router.post('/get_remain_wallet_amount', response_model=GetWallets)
async def recieve_wallet_amount(filter_wallets: FilterWallets, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_remain_wallet_amount(filter_wallets, current_user, db)
