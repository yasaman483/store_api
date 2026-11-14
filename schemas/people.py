from pydantic import BaseModel, ConfigDict, Field, field_validator
from datetime import date
from schemas.employee_info import EmployeeInfoCreate, EmployeeInfoUpdateFromPerson
from schemas.employee_info import EmployeeInfoResponse
from enum import Enum
import re
from fastapi import Query
from decimal import Decimal
from schemas.wallet import SortOrder


class PersonStatus(str, Enum):
    ACTIVE = 'active'
    UNACTIVE = 'unactive'


class Roles(str, Enum):
    MANAGER = 'manager'
    EMPLOYEE = 'employee'
    CUSTOMER = 'customer'


class SortByPeople(str, Enum):
    USER_ID = "user_id"
    ROLE = "role"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    BIRTH_DATE = "birth_date"
    PHONE = "phone"
    ADDRESS = "address"
    CITY = "city"
    PERSON_STATUS = "person_status"

    @classmethod
    def _missing_(cls, value):
        return cls.USER_ID


class PersonBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    birth_date: date
    phone: str = Field(min_length=11, max_length=11, pattern=r"^09[0-9]{9}$")
    address: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)
    person_status: PersonStatus | None

    @field_validator("birth_date")
    @classmethod
    def validate_date(cls, value: date):
        output = re.search(
            r'[0-9]{4}/[0-9]{2}/[0-9]{2}', value.strftime("%Y/%m/%d"))
        if output:
            return value
        else:
            raise ValueError(f"{value} doesn't have true format")


class PersonCreate(PersonBase):
    password: str = Field(min_length=8)
    employee_info: EmployeeInfoCreate | None = None


class PersonUpdate(BaseModel):
    user_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    birth_date: date | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    person_status: PersonStatus | None = None
    employee_info: EmployeeInfoUpdateFromPerson | None = None


class PersonResponse(PersonBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role: Roles


class FullPersonInfo(BaseModel):
    person: PersonResponse
    employee_info: EmployeeInfoResponse | None


class GetPeopleInfo(BaseModel):
    people: list[FullPersonInfo]
    page: int
    page_size: int
    total: int
    pages: int


class LoginRequest(BaseModel):
    phone: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: PersonResponse


class GetId(BaseModel):
    user_id: int


class FilterPeople(BaseModel):
    page: int = Query(1, ge=1)
    page_size: int = Query(1, ge=1, le=100)
    user_id: int | None = Query(None)
    role: Roles | None = Query(None)
    first_name: str | None = Query(None)
    last_name: str | None = Query(None)
    before_date_birth_date: date | None = Query(None)
    after_date_birth_date: date | None = Query(None)
    phone: str | None = Query(None)
    address: str | None = Query(None)
    city: str | None = Query(None)
    person_status: PersonStatus | None = Query(None)
    job_title: str | None = Query(None)
    min_salary: Decimal | None = Query(None)
    max_salary: Decimal | None = Query(None)
    sort_by: SortByPeople = Query(SortByPeople.USER_ID)
    sort_order: SortOrder = Query(SortOrder.ASC)
