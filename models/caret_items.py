from sqlalchemy import INTEGER, Date, ForeignKey, DECIMAL, func, Enum as SQLEnum
from sqlalchemy.orm import mapped_column, Mapped, relationship
from database.connect import Base
from decimal import Decimal
from datetime import date
from schemas.caret_items import CaretItemStatus


class CaretItems(Base):
    __tablename__ = "caret_items"

    caret_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("carets.caret_id", ondelete="cascade"), primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("products.product_id", ondelete="cascade"), primary_key=True, nullable=False)
    quantity: Mapped[int] = mapped_column(INTEGER, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(12, 2), nullable=False)
    caret_item_status: Mapped[CaretItemStatus] = mapped_column(SQLEnum(
        CaretItemStatus), nullable=False, server_default=CaretItemStatus.UNCHECKED)
    date_: Mapped[date] = mapped_column(Date, server_default=func.now())

    caret = relationship("Caret", back_populates="caret_items")
