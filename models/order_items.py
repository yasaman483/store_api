from sqlalchemy import Integer, DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connect import Base
from decimal import Decimal


class OrderItems(Base):
    __tablename__ = 'order_items'

    order_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        "orders.order_id", ondelete='cascade'), primary_key=True,  nullable=False)
    product_id: Mapped[int] = mapped_column(Integer, ForeignKey(
        "products.product_id", ondelete='cascade'), primary_key=True, nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)

    order = relationship("Orders", back_populates="order_items")
