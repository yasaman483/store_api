from sqlalchemy import String, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database.connect import Base
from schemas.categories import CategoryCondition


class Category(Base):
    __tablename__ = 'categories'

    category_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    category_name: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True)
    category_situation: Mapped[CategoryCondition] = mapped_column(
        SQLEnum(CategoryCondition), nullable=False, default=CategoryCondition.ACTIVE)

    products = relationship(
        "Product", back_populates="product_category")
