from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, Date, DECIMAL, Boolean, Enum as SQLEnum
from database.connect import Base
from schemas.discount import DiscountType
from decimal import Decimal
from datetime import date


class Discount(Base):
    __tablename__ = 'discount'

    discount_id: Mapped[int] = mapped_column(
        Integer, autoincrement=True, nullable=False, primary_key=True)
    discount_name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True)
    discount_type: Mapped[DiscountType] = mapped_column(SQLEnum(DiscountType))
    amount: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    expired_at: Mapped[date] = mapped_column(Date, nullable=False)
    active_for_all: Mapped[bool] = mapped_column(Boolean, nullable=False)

    discount_people = relationship(
        "DiscountPeople", back_populates="discount", cascade="all, delete-orphan")
