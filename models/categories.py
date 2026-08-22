from sqlalchemy import String, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connect import Base


class Category(Base):
    __tablename__ = 'categories'

    category_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True)

    products = relationship(
        "Product", back_populates="product_category")
