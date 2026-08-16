from pydantic import BaseModel, ConfigDict
from datetime import date
from enum import Enum


class DiscountStatus(str, Enum):
    ACTIVE = "active"
    DEACTIVE = "deactive"


class DiscountPeopleBase(BaseModel):
    used: bool
    used_at: date | None = None
    discount_id: int
    people_id: int


class DiscountPeopleCreate(DiscountPeopleBase):
    pass


class DiscountPeopleUpdate(BaseModel):
    phone: str
    status: DiscountStatus


class DiscountPeopleResponse(DiscountPeopleBase):
    model_config = ConfigDict(from_attributes=True)

    order_id: int | None


class GetDiscountId(BaseModel):
    discount_id: int
