from sqlalchemy import Integer, Boolean, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import date
from database.connect import Base


class DiscountPeople(Base):
    __tablename__ = 'discount_people'

    discount_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        "discount.discount_id", ondelete="cascade"), primary_key=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.order_id", ondelete="set null"), nullable=True, default=None)
    people_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        "people.people_id", ondelete="cascade"), primary_key=True)
    used: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    used_at: Mapped[date] = mapped_column(Date, nullable=True, default=None)

    discount = relationship("Discount", back_populates="discount_people")
    people = relationship("People", back_populates="discount_people")
