from fastapi import Query
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from enum import Enum
from schemas.wallet import SortOrder


class SortByProduct(str, Enum):
    PRODUCT_ID = "product_id"
    PRODUCT_NAME = "product_name"
    UNIT_PRICE = "unit_price"
    REMAIN_IN_STOCK = "remain_in_stock"
    CATEGORY_ID = "category_id"
    PRODUCT_STATUS = "product_status"

    @classmethod
    def _missing_(cls, value):
        return cls.PRODUCT_ID


class ProductStatus(str, Enum):
    ACTIVE = "active"
    UNACTIVE = "unactive"


class ProductBase(BaseModel):
    product_name: str = Field(min_length=1, max_length=50, unique=True)
    unit_price: Decimal
    remain_in_stock: int
    product_status: ProductStatus


class ProductCreate(ProductBase):
    category_name: str


class ProductUpdateGet(BaseModel):
    product_name: str | None = None
    unit_price: Decimal | None = None
    remain_in_stock: int | None = None
    reserved: int | None = None
    category_name: str | None = None
    product_status: ProductStatus | None = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    product_id: int
    category_id: int
    reserved: int


class GetProductId(BaseModel):
    product_id: int


class FilterProduct(BaseModel):
    page: int = Query(ge=1)
    page_size: int = Query(ge=1, le=100)
    product_id: int | None = Query(None)
    product_name: str | None = Query(None)
    min_unit_price: Decimal | None = Query(None)
    max_unit_price: Decimal | None = Query(None)
    min_remain_in_stock: int | None = Query(None)
    max_remain_in_stock: int | None = Query(None)
    category_name: str | None = Query(None)
    product_status: ProductStatus | None = Query(None)
    sort_by: SortByProduct = Query(SortByProduct.PRODUCT_ID)
    sort_order: SortOrder = Query(SortOrder.ASC)


class GetProduct(BaseModel):
    products: list[ProductResponse]
    page: int
    page_size: int
    total: int
    pages: int
