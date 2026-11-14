from fastapi import Query
from pydantic import BaseModel, ConfigDict
from enum import Enum
from decimal import Decimal
from datetime import date
from schemas.discount_granted import DiscountGrantedUpdate
from schemas.wallet import SortOrder


class SortByDiscount(str, Enum):
    DSICOUNT_ID = "discount_id"
    DISCOUNT_NAME = "discount_name"
    DISCOUNT_TYPE = "discount_type"
    AMOUNT = "amount"
    EXPIRED_AT = "expired_at"
    ACTIVE_FOR_ALL = "active_for_all"
    DISCOUNT_STATUS = "discount_status"

    @classmethod
    def _missing_(cls, value):
        return cls.DSICOUNT_ID


class DiscountStatus(str, Enum):
    ACTIVE = "active"
    UNACTIVE = "unactive"


class DiscountType(str, Enum):
    PERCENT = 'percent'
    AMOUNT = 'amount'


class DiscountBase(BaseModel):
    discount_name: str
    discount_type: DiscountType
    amount: Decimal
    expired_at: date
    active_for_all: bool
    discount_status: DiscountStatus


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


class FilterDiscount(BaseModel):
    page: int = Query(ge=1)
    page_size: int = Query(ge=1, le=100)
    discount_id: int | None = Query(None)
    discount_name: str | None = Query(None)
    discount_type: DiscountType | None = Query(None)
    min_amount: Decimal | None = Query(None)
    max_amount: Decimal | None = Query(None)
    expired_before_at: date | None = Query(None)
    expired_after_at: date | None = Query(None)
    active_for_all: bool | None = Query(None)
    discount_status: DiscountStatus | None = Query(None)
    sort_order: SortOrder = Query(SortOrder.ASC)
    sort_by: SortByDiscount = Query(SortByDiscount.DSICOUNT_ID)


class GetDiscount(BaseModel):
    discounts: list[DiscountResponse]
    page: int
    page_size: int
    total: int
    pages: int
