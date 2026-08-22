from pydantic import BaseModel, ConfigDict
from decimal import Decimal


class WalletBase(BaseModel):
    wallet_id: int


class WalletCreate(WalletBase):
    customer_id: int


class WalletResopnse(WalletBase):
    model_config = ConfigDict(from_attributes=True, validate_assignment=True)
    wallet_balance: Decimal


class UpdateAmount(BaseModel):
    amount: Decimal
