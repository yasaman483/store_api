from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from fastapi import Query
from schemas.wallet import SortOrder
from enum import Enum


class SortByCategory(str, Enum):
    CATEGORY_ID = "category_id"
    CATEGORY_NAME = "category_name"
    CATEGORY_SITUATION = "category_situation"

    @classmethod
    def _missing_(cls, value):
        return cls.CATEGORY_ID


class CategoryCondition(str, Enum):
    ACTIVE = "active"
    UNACTIVE = "unactive"


class CategoryBase(BaseModel):
    category_name: str = Field(min_length=1, max_length=50)


class CategoryCreate(CategoryBase):
    category_situation: CategoryCondition | None


class CategoryUpdate(BaseModel):
    category_name: str | None = None
    category_situation: CategoryCondition | None = None


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    category_id: int
    category_situation: CategoryCondition


class GetCategoryId(BaseModel):
    category_id: int


class FilterCategory(BaseModel):
    page: int = Query(ge=1)
    page_size: int = Query(ge=1, le=100)
    category_id: int = Query(None)
    category_name: str = Query(None)
    category_situation: CategoryCondition = Query(None)
    sort_order: SortOrder = Query(SortOrder.ASC)
    sort_by: SortByCategory = Query(SortByCategory.CATEGORY_ID)


class GetCategoryInfo(BaseModel):
    categories: list[CategoryResponse]
    page: int
    page_size: int
    total: int
    pages: int
