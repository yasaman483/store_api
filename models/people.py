from sqlalchemy import Integer, String, Date, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connect import Base
from datetime import date
from schemas.people import Roles


class People(Base):
    __tablename__ = "people"
    people_id: Mapped[int] = mapped_column(
        Integer, autoincrement=True, primary_key=True, nullable=False)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(200), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    phone: Mapped[str] = mapped_column(String(20), nullable=False, unique=True)
    address: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    role: Mapped[Roles] = mapped_column(SQLEnum(Roles), nullable=False)

    discount_people = relationship("DiscountPeople", back_populates="people")
