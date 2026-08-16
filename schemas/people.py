from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from schemas.report_to import ReportToCreate, ReportToUpdateFromPeople
from enum import Enum


class Roles(str, Enum):
    MANAGER = 'manager'
    EMPLOYEE = 'employee'
    CUSTOMER = 'customer'


class PeopleBase(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    birth_date: date
    phone: str = Field(min_length=11, max_length=11, pattern=r'^09[0-9]{9}$')
    address: str = Field(min_length=1, max_length=100)
    city: str = Field(min_length=1, max_length=100)


class PeopleCreate(PeopleBase):
    password: str = Field(min_length=8)
    report_to: ReportToCreate | None = None


class PeopleUpdate(BaseModel):
    people_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    password: str | None = None
    birth_date: date | None = None
    phone: str | None = None
    address: str | None = None
    city: str | None = None
    report_to: ReportToUpdateFromPeople | None = None


class PeopleResponse(PeopleBase):
    model_config = ConfigDict(from_attributes=True)

    people_id: int
    role: Roles


class LoginRequest(BaseModel):
    phone: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: PeopleResponse


class GetId(BaseModel):
    people_id: int


# class GetPhone(BaseModel):
#     phone: str
# class CustomerCreate(PeopleBase):
#     password: str = Field(min_length=8)
# class EmployeeCreate(PeopleBase):
#     password: str = Field(min_length=8)
#     report_to: ReportToCreate
# class EmployeeUpdateSent(BaseModel):
#     first_name: str | None = None
#     last_name: str | None = None
#     password: str | None = None
#     birth_date: date | None = None
#     phone: str | None = None
#     address: str | None = None
#     city: str | None = None
#     report_to: ReportToUpdate | None = None
# class CustomerUpdate(BaseModel):
#     first_name: str | None = None
#     last_name: str | None = None
#     password: str | None = None
#     birth_date: date | None = None
#     phone: str | None = None
#     address: str | None = None
#     city: str | None = None
