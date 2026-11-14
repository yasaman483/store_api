from fastapi import Query
from pydantic import BaseModel, ConfigDict
from datetime import date
from enum import Enum
from schemas.wallet import SortOrder


class SortByDiscountGranted(str, Enum):
    DISCOUNT_ID = "discount_id"
    ORDER_ID = "order_id"
    USER_ID = "user_id"
    USED = "used"
    USED_AT = "used_at"

    @classmethod
    def _missing_(cls, value):
        return cls.DISCOUNT_ID


class DiscountGrantedStatus(str, Enum):
    ACTIVE = "active"
    DEACTIVE = "deactive"


class DiscountGrantedBase(BaseModel):
    used: bool
    used_at: date | None = None
    discount_id: int
    user_id: int


class DiscountGrantedCreate(DiscountGrantedBase):
    pass


class DiscountGrantedUpdate(BaseModel):
    user_id: str
    status: DiscountGrantedStatus


class DiscountGrantedResponse(DiscountGrantedBase):
    model_config = ConfigDict(from_attributes=True)

    order_id: int | None


class GetDiscountId(BaseModel):
    discount_id: int


class DiscountGrantedFilter(BaseModel):
    page: int = Query(ge=1)
    page_size: int = Query(ge=1, le=100)
    discount_id: int | None = Query(None)
    order_id: int | None = Query(None)
    user_id: int | None = Query(None)
    used: bool | None = Query(None)
    used_at: date | None = Query(None)
    sort_order: SortOrder = Query(SortOrder.ASC)
    sort_by: SortByDiscountGranted = Query(SortByDiscountGranted.DISCOUNT_ID)


class GetDiscountGranted(BaseModel):
    discount_granted: list[DiscountGrantedResponse]
    page: int
    page_size: int
    total: int
    pages: int
