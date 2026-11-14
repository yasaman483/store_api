from sqlalchemy import Integer, DECIMAL, String, ForeignKey, func, Enum as SQLEnum, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from schemas.orders import OrderStatus, PaymentMethod, ReservationStatus
from datetime import datetime, timedelta
from database.connect import Base
from decimal import Decimal


class Order(Base):
    __tablename__ = "orders"

    order_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("people.user_id", ondelete='NO ACTION'), nullable=False)
    order_date: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.current_timestamp())
    order_status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus), nullable=False)
    reservation_status: Mapped[ReservationStatus] = mapped_column(
        SQLEnum(ReservationStatus), default=ReservationStatus.ACTIVE, nullable=False)
    payment_method: Mapped[PaymentMethod] = mapped_column(
        SQLEnum(PaymentMethod), nullable=False)
    total_amount_without_discount: Mapped[Decimal] = mapped_column(
        DECIMAL, nullable=False)
    discount: Mapped[str | None] = mapped_column(
        String(100), nullable=True, default=None)
    total_amount_discounted: Mapped[Decimal] = mapped_column(
        DECIMAL, nullable=False)
    expired_reservation_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=func.current_timestamp()+timedelta(minutes=30))

    customer = relationship(
        "Person", back_populates="orders")
    order_items = relationship("OrderItems", back_populates="order",
                               cascade="all, delete-orphan")
    payment_history = relationship(
        "PaymentHistory", back_populates="order")
