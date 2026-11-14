from fastapi import HTTPException
from models.people import Person
from sqlalchemy import select, asc, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.inspection import inspect
from models.wallet import Wallet
from schemas.wallet import UpdateWalletAmount, FilterWallets, SortOrder, GetWallets
from schemas.people import Roles, PersonStatus
import logging
from crud.audit_log import create_audit_log
from schemas.audit import AuditContext
from decimal import Decimal
from datetime import date
from math import ceil


logger = logging.getLogger(__name__)


def make_json_format(value: dict):
    for key, val in value.items():
        if isinstance(val, Decimal):
            value[key] = str(value[key])
        elif isinstance(val, date):
            value[key] = value[key].isoformat()
    return value


async def update_wallet_amount(wallet: UpdateWalletAmount, audit: AuditContext, current_user: Person, db: AsyncSession, auto_commit: bool = True):
    if current_user.role == Roles.CUSTOMER:
        user_id = current_user.user_id

        result = await db.execute(select(Person).where(Person.user_id == current_user.user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if user.person_status == PersonStatus.UNACTIVE:
            raise HTTPException(
                status_code=403, detail="The account is unactivated")

        result = await db.execute(select(Wallet).where(
            Wallet.customer_id == current_user.user_id).with_for_update())

    elif current_user.role == Roles.MANAGER or current_user.role == Roles.EMPLOYEE:
        user_id = wallet.user_id

        result = await db.execute(select(Person).where(Person.user_id == wallet.user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if user.person_status == PersonStatus.UNACTIVE:
            raise HTTPException(
                status_code=403, detail="The account is unactivated")

        result = await db.execute(select(Wallet).where(
            Wallet.customer_id == wallet.user_id).with_for_update())

    else:
        raise HTTPException(
            status_code=403, detail="Not allowed to change the wallet")

    user_wallet = result.scalar_one_or_none()

    if user_wallet is None:
        raise HTTPException(
            status_code=404, detail=f"Wallet not found")

    old_value = {column.key: getattr(user_wallet, column.key)
                 for column in inspect(Wallet).mapper.column_attrs}

    user_wallet.wallet_balance += wallet.amount
    await db.flush()

    new_value = {column.key: getattr(user_wallet, column.key)
                 for column in inspect(Wallet).mapper.column_attrs}

    new_value = make_json_format(new_value)
    old_value = make_json_format(old_value)

    try:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=user_wallet.wallet_id,
            entity_type="wallet",
            event="WALLET_UPDATED",
            old_value=old_value,
            new_value=new_value
        )

        if auto_commit:
            await db.commit()
            await db.refresh(user_wallet)
        return user_wallet

    except Exception:
        logger.exception(
            f"Amount wasn't added to the wallet successfully for user {user_id}")
        await db.rollback()
        raise


async def deduct_from_wallet(wallet: UpdateWalletAmount, audit: AuditContext, current_user: Person, db: AsyncSession):
    if wallet.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")

    if current_user.role != Roles.CUSTOMER:
        raise HTTPException(
            status_code=403, detail="Don't have permission to change the amount of the wallet")

    result = await db.execute(select(Person).where(Person.user_id == current_user.user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    if user.person_status == PersonStatus.UNACTIVE:
        raise HTTPException(
            status_code=403, detail="The account is unactivated")

    result = await db.execute(select(Wallet).where(
        Wallet.customer_id == current_user.user_id).with_for_update())

    user_wallet = result.scalar_one_or_none()

    if user_wallet is None:
        raise HTTPException(
            status_code=404, detail=f"Wallet not found for user {current_user.user_id}")

    if user_wallet.wallet_balance < wallet.amount:
        raise HTTPException(
            status_code=401, detail=f"wallet {user_wallet.customer_id} doesn't have enough balance")

    old_value = {column.key: getattr(user_wallet, column.key)
                 for column in inspect(Wallet).mapper.column_attrs}

    user_wallet.wallet_balance -= wallet.amount
    await db.flush()

    new_value = {column.key: getattr(user_wallet, column.key)
                 for column in inspect(Wallet).mapper.column_attrs}

    old_value = make_json_format(old_value)
    new_value = make_json_format(new_value)

    try:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=user_wallet.wallet_id,
            entity_type="wallet",
            event="WALLET_DEDUCTED",
            old_value=old_value,
            new_value=new_value
        )

        await db.commit()
        await db.refresh(user_wallet)

        return user_wallet

    except Exception:
        logger.exception(
            f"Deduction form wallet {user_wallet.wallet_id} failed")
        raise


async def get_remain_wallet_amount(filter_wallets: FilterWallets, current_user: Person, db: AsyncSession):
    if current_user.role == Roles.CUSTOMER:
        result = await db.execute(select(Person).where(Person.user_id == current_user.user_id))
        user = result.scalar_one_or_none()

        if user is None:
            raise HTTPException(status_code=404, detail="User not found")

        if user.person_status == PersonStatus.UNACTIVE:
            raise HTTPException(
                status_code=403, detail="The account is unactivated")

        result = await db.execute(select(Wallet).where(
            Wallet.customer_id == current_user.user_id))

        user_wallet = result.scalar_one_or_none()

        if user_wallet is None:
            raise HTTPException(
                status_code=404, detail=f"Wallet not found for user {current_user.user_id}")

        return GetWallets(wallets=[user_wallet], page=filter_wallets.page, page_size=filter_wallets.page_size, total=1, pages=1)

    elif current_user.role == Roles.MANAGER or current_user.role == Roles.EMPLOYEE:
        filters = []
        if filter_wallets.wallet_id is not None:
            filters.append(Wallet.wallet_id == filter_wallets.wallet_id)
        if filter_wallets.customer_id is not None:
            filters.append(Wallet.customer_id == filter_wallets.customer_id)
        if filter_wallets.min_wallet_balance is not None:
            filters.append(Wallet.wallet_balance >=
                           filter_wallets.min_wallet_balance)
        if filter_wallets.max_wallet_balance is not None:
            filters.append(Wallet.wallet_balance <=
                           filter_wallets.max_wallet_balance)

        query = select(Wallet).where(*filters)
        result = select(func.count()).select_from(query.subquery())
        total = await db.scalar(result)
        offset = (filter_wallets.page - 1)*filter_wallets.page_size

        if filter_wallets.sort_order == SortOrder.ASC:
            query = query.order_by(asc(filter_wallets.sort_by)).offset(
                offset).limit(filter_wallets.page_size)
        else:
            query = query.order_by(desc(filter_wallets.sort_by)).offset(
                offset).limit(filter_wallets.page_size)

        result = await db.execute(query)
        wallets = result.scalars().all()

        if not wallets:
            raise HTTPException(status_code=404, detail="No wallet found")

        return GetWallets(wallets=wallets, page=filter_wallets.page, page_size=filter_wallets.page_size, total=total, pages=ceil(total/filter_wallets.page_size))

    else:
        raise HTTPException(
            status_code=403, detail="Don't have premmision to get the amount of the wallet")
