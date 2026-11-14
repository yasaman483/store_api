from pydantic import BaseModel, ConfigDict, field_validator
from decimal import Decimal


class OrderItemsBase(BaseModel):
    quantity: int


class OrderItemsCreate(OrderItemsBase):
    product_name: str


class OrderItemsUpdate(BaseModel):
    product_name: str
    quantity: int

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, value: int):
        if value < 0:
            raise ValueError("Quantity shouldn't be less than zero")
        return value


class OrderItemsDelete(BaseModel):
    product_name: str


class OrderItemsResponse(OrderItemsBase):
    model_config = ConfigDict(from_attributes=True)

    order_id: int
    unit_price: Decimal
    product_id: int
