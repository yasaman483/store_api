from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import INTEGER, DECIMAL, ForeignKey
from database.connect import Base
from decimal import Decimal


class Wallet(Base):
    __tablename__ = "wallets"

    wallet_id: Mapped[int] = mapped_column(
        INTEGER, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("people.user_id", ondelete="cascade"), nullable=False, unique=True)
    wallet_balance: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 2), nullable=False, default=0)

    customer = relationship(
        "Person", back_populates="person")
