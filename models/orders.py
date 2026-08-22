from sqlalchemy import Integer, Date, DECIMAL, String, ForeignKey, func, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from schemas.orders import OrderStatus, PaymentMethod
from datetime import date
from database.connect import Base
from decimal import Decimal


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("people.user_id", ondelete='cascade'), nullable=False)
    order_date: Mapped[date] = mapped_column(
        Date, server_default=func.now())
    order_status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus), nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod), nullable=False)
    total_amount_without_discount: Mapped[Decimal] = mapped_column(
        DECIMAL, nullable=False)
    discount: Mapped[str] = mapped_column(
        String(100), nullable=True, default=None)
    total_amount_discounted: Mapped[Decimal] = mapped_column(
        DECIMAL, nullable=False)

    customer = relationship(
        "Person", back_populates="orders")
    order_items = relationship("OrderItems", back_populates="order",
                               cascade="all, delete-orphan")
    payment_history = relationship(
        "PaymentHistory", back_populates="order")
