from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import INTEGER, DECIMAL, ForeignKey
from database.connect import Base
from decimal import Decimal


class Wallet(Base):
    __tablename__ = "wallet"

    wallet_id: Mapped[int] = mapped_column(
        INTEGER, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(
        INTEGER, ForeignKey("people.people_id", ondelete="cascade"), nullable=False, unique=True)
    wallet_balance: Mapped[Decimal] = mapped_column(
        DECIMAL(12, 2), nullable=False, default=0)
