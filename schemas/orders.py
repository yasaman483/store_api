from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from schemas.order_items import OrderItemsCreate
from decimal import Decimal
from enum import Enum


class OrderStatus(str, Enum):
    UNCONFIRMED = "unconfirmed"
    CONFIRMED = "confirmed"
    PENDING = "pending"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentMethod(str, Enum):
    ONLINE = "online"
    CASH = "cash"
    WALLET = "wallet"


class OrdersBase(BaseModel):
    pass


class OrdersCreate(OrdersBase):
    items: list[OrderItemsCreate]
    payment_method: str
    discount: str | None = None


class OrdersResponse(OrdersBase):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    customer_id: int
    order_status: OrderStatus = Field(default=OrderStatus.UNCONFIRMED)
    order_date: date
    total_amount_without_discount: Decimal
    total_amount_discounted: Decimal
    payment_method: PaymentMethod


class OrderUpdateById(OrdersBase):
    order_id: int


class OrderUpdateByStatus(BaseModel):
    order_status: OrderStatus
