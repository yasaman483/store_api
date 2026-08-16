from sqlalchemy import Integer, String, ForeignKey, DECIMAL, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from database.connect import Base
from decimal import Decimal
from schemas.report_to import EmployeeStatus


class ReportTo(Base):
    __tablename__ = "report_to"

    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("people.people_id", ondelete='cascade'), primary_key=True)
    job_title: Mapped[str] = mapped_column(String(50), nullable=False)
    salary: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    employee_status: Mapped[EmployeeStatus] = mapped_column(
        SQLEnum(EmployeeStatus), nullable=False)
