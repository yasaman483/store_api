from sqlalchemy import Integer, String, ForeignKey, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connect import Base
from decimal import Decimal


class EmployeeInfo(Base):
    __tablename__ = "employees_info"

    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("people.user_id", ondelete='cascade'), primary_key=True)
    job_title: Mapped[str] = mapped_column(String(50), nullable=False)
    salary: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)

    employee = relationship(
        "Person", back_populates="employee_info")
