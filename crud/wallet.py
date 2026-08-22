from fastapi import HTTPException
from models.people import Person
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.wallet import Wallet
from schemas.wallet import UpdateAmount
from decimal import Decimal
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)


async def update_wallet_amount(added_amount: UpdateAmount, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if added_amount.amount < 0:
        raise HTTPException(status_code=401, detail="Amount must be positive.")

    result = await db.execute(select(Wallet).where(
        Wallet.customer_id == current_user.user_id))

    user_wallet = result.scalar_one_or_none()

    if user_wallet is None:
        raise HTTPException(
            status_code=404, detail=f"Wallet not found for user {current_user.user_id}")

    user_wallet.wallet_balance += added_amount.amount

    try:
        await db.commit()
        await db.refresh(user_wallet)
        end_time = datetime.now(UTC)
        duration_time = (end_time - start_time).total_seconds()
        info = {
            "event": "Amount added successfully",
            "path": "/Wallet/update_wallet_amount",
            "user_id": user_wallet.customer_id,
            "status_code": 200,
            "duration_s": duration_time
        }
        logger.info(info)
        return user_wallet
    except Exception as e:
        end_time = datetime.now(UTC)
        duration_time = (end_time - start_time).total_seconds()
        error = {
            "event": "Amount wasn't added to the wallet",
            "path": "/Wallet/update_wallet_amount",
            "user_id": user_wallet.customer_id,
            "duration_s": duration_time
        }
        logger.error(error)
        await db.rollback()
        raise e


async def deduct_from_wallet(amount: Decimal, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if amount < 0:
        raise HTTPException(status_code=401, detail="Amount must be positive")

    result = await db.execute(select(Wallet).where(
        Wallet.customer_id == current_user.user_id))

    user_wallet = result.scalar_one_or_none()

    if user_wallet is None:
        raise HTTPException(
            status_code=404, detail=f"Wallet not found for user {current_user.user_id}")

    if user_wallet.wallet_balance < amount:
        raise HTTPException(
            status_code=401, detail="wallet doesn't have enough balance")

    user_wallet.wallet_balance -= amount

    try:
        end_time = datetime.now(UTC)
        duration_time = (end_time - start_time).total_seconds()
        info = {
            "event": "Amount deducted successfully",
            "method": "POST",
            "path": "/Orders/add_order",
            "user_id": user_wallet.customer_id,
            "status_code": 200,
            "duration_s": duration_time
        }
        logger.info(info)
        await db.commit()
        await db.refresh(user_wallet)
        return user_wallet
    except Exception as e:
        end_time = datetime.now(UTC)
        duration_time = (end_time - start_time).total_seconds()
        error = {
            "event": "Amount wasn't deducted successfully",
            "method": "POST",
            "path": "/Orders/add_order",
            "user_id": user_wallet.customer_id,
            "status_code": 200,
            "duration_s": duration_time
        }
        logger.error(error)
        await db.rollback()
        raise e


async def get_remain_wallet_amount(current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    result = await db.execute(select(Wallet).where(
        Wallet.customer_id == current_user.user_id))

    user_wallet = result.scalar_one_or_none()

    if user_wallet is None:
        raise HTTPException(
            status_code=404, detail=f"Wallet not found for user {current_user.user_id}")

    end_time = datetime.now(UTC)
    duration_time = (end_time - start_time).total_seconds()
    info = {
        "event": "Remain wallet amount sent successfully",
        "method": "POST",
        "path": "/Wallet/get_remain_wallet_amount",
        "user_id": user_wallet.customer_id,
        "status_code": 200,
        "duration_s": duration_time
    }
    logger.info(info)
    return user_wallet.wallet_balance
