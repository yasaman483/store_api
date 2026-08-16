from pydantic import BaseModel, ConfigDict, Field
from decimal import Decimal
from datetime import date
from enum import Enum


class PaymentStatus(str, Enum):
    SUCCESS = 'success'
    FAILED = 'failed'
    PENDING = 'pending'


class PaymentHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    payment_id: int
    order_id: int
    payment_status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    payment_date: date | None
    payment_amount: Decimal


class GetPaymentHistoryId(BaseModel):
    payment_id: int
