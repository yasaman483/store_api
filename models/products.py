from sqlalchemy import String, Integer, DECIMAL, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connect import Base
from decimal import Decimal
from schemas.products import ProductStatus


class Product(Base):
    __tablename__ = "products"

    product_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    product_name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True)
    unit_price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)
    remain_in_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.category_id", ondelete="SET NULL"), nullable=True)
    product_status: Mapped[ProductStatus] = mapped_column(
        SQLEnum(ProductStatus), nullable=False, default=ProductStatus.ACTIVE)

    product_category = relationship(
        "Category", back_populates='products')
    order_items = relationship(
        "OrderItems", back_populates="products")
