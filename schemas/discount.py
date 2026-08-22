from pydantic import BaseModel, ConfigDict
from enum import Enum
from decimal import Decimal
from datetime import date
from schemas.discount_granted import DiscountGrantedUpdate


class DiscountType(str, Enum):
    PERCENT = 'percent'
    AMOUNT = 'amount'


class DiscountBase(BaseModel):
    discount_name: str
    discount_type: DiscountType
    amount: Decimal
    expired_at: date
    active_for_all: bool


class DiscountCreate(DiscountBase):
    people: list[str]


class DiscountResponse(DiscountBase):
    model_config = ConfigDict(from_attributes=True)

    discount_id: int


class DiscountUpdateGet(BaseModel):
    discount_name: str


class DiscountUpdateSent(BaseModel):
    discount_name: str | None = None
    discount_type: DiscountType | None = None
    amount: Decimal | None = None
    expired_at: date | None = None
    active_for_all: bool | None = None
    people: list[DiscountGrantedUpdate] | None = None


class GetDiscountName(BaseModel):
    discount_name: str


class GetDiscountId(BaseModel):
    discount_id: int
