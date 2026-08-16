from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from enum import Enum


class EmployeeStatus(str, Enum):
    ACTIVE = 'active'
    UNACTIVE = 'unactive'


class ReportToBase(BaseModel):
    job_title: str = Field(min_length=1, max_length=50, nullable=False)
    salary: Decimal


class ReportToCreate(ReportToBase):
    pass


class ReportToResponse(ReportToBase):
    model_config = ConfigDict(from_attributes=True)

    employee_id: int
    employee_status: EmployeeStatus = EmployeeStatus.ACTIVE


class ReportToUpdateFromPeople(BaseModel):
    job_title: str | None = None
    salary: Decimal | None = None
    employee_status: EmployeeStatus | None = None


class ReportToUpdate(ReportToUpdateFromPeople):
    employee_id: int


class GetEmployeeId(BaseModel):
    employee_id: int
