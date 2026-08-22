from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from schemas.employee_info import EmployeeInfoCreate, EmployeeInfoUpdateFromPerson
from enum import Enum


class Roles(str, Enum):
    MANAGER = 'manager'
    EMPLOYEE = 'employee'
    CUSTOMER = 'customer'


class PersonBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    birth_date: date
    phone: str = Field(min_length=11, max_length=11, pattern=r'^09[0-9]{9}$')
    address: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)


class PersonCreate(PersonBase):
    password: str = Field(min_length=8)
    report_to: EmployeeInfoCreate | None = None


class PersonUpdate(BaseModel):
    user_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    birth_date: date | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    report_to: EmployeeInfoUpdateFromPerson | None = None


class PersonResponse(PersonBase):
    model_config = ConfigDict(from_attributes=True)

    user_id: int
    role: Roles


class LoginRequest(BaseModel):
    phone: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: PersonResponse


class GetId(BaseModel):
    user_id: int
