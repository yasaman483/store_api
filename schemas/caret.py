from pydantic import BaseModel, ConfigDict
from schemas.caret_items import CaretItemsResponse
from schemas.wallet import SortOrder
from enum import Enum
from datetime import date
from fastapi import Query
from decimal import Decimal
from schemas.caret_items import CaretItemStatus


class SortByCaret(str, Enum):
    CARET_ID = "caret_id"
    USER_ID = "user_id"

    @classmethod
    def _missing_(cls, value):
        return cls.CARET_ID


class CaretBase(BaseModel):
    caret_id: int
    user_id: int


class CaretResponse(CaretBase):
    model_config = ConfigDict(from_attributes=True)

    caret_items: list[CaretItemsResponse]


class FilterCaret(BaseModel):
    page: int = Query(1, ge=1)
    page_size: int = Query(1, ge=1, le=100)
    caret_id: int | None = Query(None)
    user_id: int | None = Query(None)
    product_id: int | None = Query(None)
    min_quantity: int | None = Query(None)
    max_quantity: int | None = Query(None)
    min_unit_price: Decimal | None = Query(None)
    max_unit_price: Decimal | None = Query(None)
    before_date_: date | None = Query(None)
    after_date_: date | None = Query(None)
    caret_item_status: CaretItemStatus | None = Query(None)
    sort_by: SortByCaret = Query(SortByCaret.CARET_ID)
    sort_order: SortOrder = Query(SortOrder.ASC)


class GetCarets(BaseModel):
    carets: list[CaretResponse]
    page: int
    page_size: int
    total: int
    pages: int
