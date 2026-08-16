from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    category_name: str = Field(min_length=1, max_length=50)


class CategoryCreate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    category_id: int


class GetCategoryId(BaseModel):
    category_id: int
