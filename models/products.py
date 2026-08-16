from sqlalchemy import String, Integer, DECIMAL, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connect import Base
from decimal import Decimal


class Products(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True)
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    remain_in_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.category_id", ondelete='cascade'), nullable=False)

    product_category = relationship(
        "Categories", back_populates='products')
