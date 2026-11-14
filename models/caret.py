from sqlalchemy import INTEGER, ForeignKey
from sqlalchemy.orm import mapped_column, Mapped, relationship
from database.connect import Base


class Caret(Base):
    __tablename__ = "carets"

    caret_id: Mapped[int] = mapped_column(
        INTEGER, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("people.user_id", ondelete="cascade"), nullable=False)

    caret_items = relationship("CaretItems", back_populates="caret",
                               cascade="all, delete-orphan")
    customer = relationship("Person", back_populates="caret")
