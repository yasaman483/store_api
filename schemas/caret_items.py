from pydantic import ConfigDict, BaseModel
from decimal import Decimal
from datetime import date
from enum import Enum
from fastapi import Query
from schemas.wallet import SortOrder
from schemas.products import GetProductId
from schemas.orders import PaymentMethod
from schemas.products import GetProductId


class SortByCaretItems(str, Enum):
    CARET_ID = "caret_id"
    PRODUCT_ID = "product_id"
    QUANTITY = "quantity"
    UNIT_PRICE = "unit_price"
    CARET_ITEM_STATUS = "caret_item_status"
    DATE = "date_"

    @classmethod
    def _missing_(cls, value):
        return cls.CARET_ID


class CaretItemStatus(str, Enum):
    UNCHECKED = "unchecked"
    CHECKED = "checked"
    DELETED = "deleted"


class CaretItemsBase(BaseModel):
    pass


class CaretItemsCreate(CaretItemsBase):
    product_id: int
    quantity: int


class InfoCaretItems(CaretItemsBase):
    user_id: int
    items: list[CaretItemsCreate]


class CaretItemsResponse(CaretItemsBase):
    model_config = ConfigDict(from_attributes=True)

    caret_id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    caret_item_status: CaretItemStatus
    date_: date


class RemoveCaretItems(BaseModel):
    caret_id: int
    products: list[GetProductId]


class CaretItemUpdateStatus(BaseModel):
    caret_id: int | None = None
    payment_method: PaymentMethod
    discount: str | None = None
    items: list[GetProductId]


class FilterCaretItems(BaseModel):
    page: int = Query(1, ge=1)
    page_size: int = Query(1, ge=1, le=100)
    caret_id: int | None = Query(None)
    product_id: int | None = Query(None)
    min_quantity: int | None = Query(None)
    max_quantity: int | None = Query(None)
    min_unit_price: Decimal | None = Query(None)
    max_unit_price: Decimal | None = Query(None)
    caret_item_status: CaretItemStatus | None = Query(None)
    before_date_: date | None = Query(None)
    after_date_: date | None = Query(None)
    sort_by: SortByCaretItems = Query(SortByCaretItems.CARET_ID)
    sort_order: SortOrder = Query(SortOrder.ASC)


class GetCaretItems(BaseModel):
    items: list[CaretItemsResponse]
    page: int
    page_size: int
    total: int
    pages: int
