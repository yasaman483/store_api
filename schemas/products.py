from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal


class ProductsBase(BaseModel):
    product_name: str = Field(min_length=1, max_length=50, unique=True)
    unit_price: Decimal
    remain_in_stock: int


class ProductsCreate(ProductsBase):
    category_name: str


class ProductsUpdateGet(BaseModel):
    product_name: str | None = None
    unit_price: Decimal | None = None
    remain_in_stock: int | None = None
    category_name: str | None = None


class ProductsUpdateSent(BaseModel):
    product_name: str | None = None


class ProductsResponse(ProductsBase):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    category_id: int


class GetProductName(BaseModel):
    product_name: str


class GetProductId(BaseModel):
    product_id: int
