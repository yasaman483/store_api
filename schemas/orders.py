from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field
from datetime import datetime
from schemas.order_items import OrderItemsCreate, OrderItemsResponse
from decimal import Decimal
from enum import Enum
from schemas.wallet import SortOrder


class SortByOrder(str, Enum):
    ORDER_ID = "order_id"
    CUSTOMER_ID = "customer_id"
    ORDER_STATUS = "order_status"
    ORDER_DATE = "order_date"
    Payment_Method = "payment_method"
    DISCOUNT = "discount"
    TOTAL_AMOUNT_WITHOUT_DISCOUNT = "total_amount_without_discount"
    TOTAL_AMOUNT_DISCOUNTED = "total_amount_discounted"

    @classmethod
    def _missing_(cls, value):
        return cls.ORDER_ID


class OrderStatus(str, Enum):
    UNCONFIRMED = "unconfirmed"
    CONFIRMED = "confirmed"
    PENDING = "pending"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUND_DELIVERED = "refund_delivered"


class ReservationStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"


class PaymentMethod(str, Enum):
    ONLINE = "online"
    CASH = "cash"
    WALLET = "wallet"


class OrderBase(BaseModel):
    pass


class OrderCreate(OrderBase):
    items: list[OrderItemsCreate]
    payment_method: str
    discount: str | None = None


class OrderResponse(OrderBase):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    customer_id: int
    order_status: OrderStatus = Field(default=OrderStatus.UNCONFIRMED)
    order_date: datetime
    total_amount_without_discount: Decimal
    total_amount_discounted: Decimal
    payment_method: PaymentMethod
    reservation_status: ReservationStatus
    expired_reservation_at: datetime


class FullOrderResponse(OrderBase):
    orders: OrderResponse
    order_items: list[OrderItemsResponse]


class OrderUpdateById(OrderBase):
    order_id: int


class OrderUpdateByStatus(BaseModel):
    order_status: OrderStatus


class FilterOrderInfo(BaseModel):
    page: int = Query(ge=1)
    page_size: int = Query(ge=1, le=100)
    order_id: int | None = Query(None)
    customer_id: int | None = Query(None)
    order_status: OrderStatus | None = Query(None)
    order_date_before_date: datetime | None = Query(None)
    order_date_after_date: datetime | None = Query(None)
    min_total_amount_without_discount: Decimal | None = Query(None)
    max_total_amount_without_discount: Decimal | None = Query(None)
    min_total_amount_discounted: Decimal | None = Query(None)
    max_total_amount_discounted: Decimal | None = Query(None)
    payment_method: PaymentMethod | None = Query(None)
    sort_by: SortByOrder = Query(SortByOrder.ORDER_ID)
    sort_order: SortOrder = Query(SortOrder.ASC)


class GetOrderInfo(BaseModel):
    orders: list[FullOrderResponse]
    page: int
    page_size: int
    total: int
    pages: int
