from pydantic import BaseModel, ConfigDict
from decimal import Decimal
from pydantic import field_validator
from enum import Enum
from fastapi import Query


class SortByWallet(str, Enum):
    WALLET_ID = "wallet_id"
    CUSTOMER_ID = "customer_id"
    WALLET_BALANCE = "wallet_balance"

    @classmethod
    def _missing_(cls, value):
        return cls.WALLET_ID


class SortOrder(str, Enum):
    ASC = "asc"
    DES = "desc"


class FilterWallets(BaseModel):
    page: int = Query(1, ge=1)
    page_size: int = Query(5, ge=1, le=100)
    wallet_id: int | None = Query(None)
    customer_id: int | None = Query(None)
    min_wallet_balance: Decimal | None = Query(None)
    max_wallet_balance: Decimal | None = Query(None)
    sort_by: SortByWallet = Query(SortByWallet.WALLET_ID)
    sort_order: SortOrder = Query(SortOrder.ASC)


class WalletBase(BaseModel):
    wallet_id: int


class WalletResponse(WalletBase):
    model_config = ConfigDict(from_attributes=True, validate_assignment=True)

    wallet_balance: Decimal
    customer_id: int


class UpdateWalletAmount(BaseModel):
    user_id: int
    amount: Decimal

    @field_validator("amount")
    @classmethod
    def validate_amount(cls, value):
        if value <= 0:
            raise ValueError("Amount must be positive")
        return value


class GetWallets(BaseModel):
    wallets: list[WalletResponse]
    page: int
    page_size: int
    total: int
    pages: int
