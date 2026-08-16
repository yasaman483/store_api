from fastapi import HTTPException
from models.people import People
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.wallet import Wallet
from schemas.wallet import UpdateAmount
from decimal import Decimal


async def update_wallet_amount(added_amount: UpdateAmount, current_user: People, db: AsyncSession):
    if added_amount.amount < 0:
        raise HTTPException(status_code=401, detail="Amount must be positive.")

    result = await db.execute(select(Wallet).where(
        Wallet.customer_id == current_user.people_id))

    user_wallet = result.scalar_one_or_none()

    if user_wallet is None:
        raise HTTPException(
            status_code=404, detail=f"Wallet not found for user {current_user.people_id}")

    user_wallet.wallet_balance += added_amount.amount

    try:
        await db.commit()
        await db.refresh(user_wallet)
        return user_wallet
    except Exception as e:
        await db.rollback()
        raise e


async def deduct_from_wallet(amount: Decimal, current_user: People, db: AsyncSession):
    if amount < 0:
        raise HTTPException(status_code=401, detail="Amount must be positive")

    result = await db.execute(select(Wallet).where(
        Wallet.customer_id == current_user.people_id))

    user_wallet = result.scalar_one_or_none()

    if user_wallet is None:
        raise HTTPException(
            status_code=404, detail=f"Wallet not found for user {current_user.people_id}")

    if user_wallet.wallet_balance < amount:
        raise HTTPException(
            status_code=401, detail="wallet doesn't have enough balance")

    user_wallet.wallet_balance -= amount

    try:
        await db.commit()
        await db.refresh(user_wallet)
        return user_wallet
    except Exception as e:
        await db.rollback()
        raise e


async def get_remain_wallet_amount(current_user: People, db: AsyncSession):
    result = await db.execute(select(Wallet).where(
        Wallet.customer_id == current_user.people_id))

    user_wallet = result.scalar_one_or_none()

    if user_wallet is None:
        raise HTTPException(
            status_code=404, detail=f"Wallet not found for user {current_user.people_id}")

    return user_wallet.wallet_balance
