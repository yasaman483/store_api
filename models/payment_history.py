from sqlalchemy import Integer, DECIMAL, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connect import Base
from decimal import Decimal
from datetime import datetime
from schemas.payment_history import PaymentStatus


class PaymentHistory(Base):
    __tablename__ = 'payment_history'
    payment_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.order_id", ondelete='cascade'), nullable=False)
    payment_status: Mapped[PaymentStatus] = mapped_column(
        SQLEnum(PaymentStatus), nullable=False)
    payment_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(10, 2), nullable=False)
    payment_date: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True)

    order = relationship(
        "Order", back_populates="payment_history")
