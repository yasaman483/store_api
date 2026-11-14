from fastapi import Query
from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from datetime import date
from enum import Enum
from schemas.wallet import SortOrder


class SortByPaymentHistory(str, Enum):
    PAYMENT_ID = "payment_id"
    ORDER_ID = "order_id"
    PAYMENT_STATUS = "payment_status"
    PAYMENT_AMOUNT = "payment_amount"
    PAYMENT_DATE = "payment_date"

    @classmethod
    def _missing_(cls, value):
        return cls.PAYMENT_ID


class PaymentStatus(str, Enum):
    SUCCESS = 'success'
    FAILED = 'failed'
    PENDING = 'pending'
    CANCELLED = "cancelled"
    REFUND = "refund"


class PaymentHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: int
    order_id: int
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    payment_date: date | None
    payment_amount: Decimal


class FilterPaymentHistory(BaseModel):
    page: int = Query(ge=1)
    page_size: int = Query(ge=1, le=100)
    payment_id: int | None = Query(None)
    order_id: int | None = Query(None)
    payment_status: PaymentStatus | None = Query(None)
    min_payment_amount: Decimal | None = Query(None)
    max_payment_amount: Decimal | None = Query(None)
    payment_befor_date: date | None = Query(None)
    payment_after_date: date | None = Query(None)
    sort_order: SortOrder = Query(SortOrder.ASC)
    sort_by: SortByPaymentHistory = Query(SortByPaymentHistory.PAYMENT_ID)


class GetPaymentHistory(BaseModel):
    payment_histories: list[PaymentHistoryResponse]
    page: int
    page_size: int
    total: int
    pages: int
