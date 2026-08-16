from pydantic import BaseModel, ConfigDict
from decimal import Decimal


class OrderItemsBase(BaseModel):
    quantity: int


class OrderItemsCreate(OrderItemsBase):
    product_name: str


class OrderItemsUpdate(BaseModel):
    product_name: str
    quantity: int


class OrderItemsDelete(BaseModel):
    product_name: str


class OrderItemsResponse(OrderItemsBase):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    unit_price: Decimal
    product_id: int
