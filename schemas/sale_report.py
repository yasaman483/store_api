from pydantic import BaseModel, ConfigDict
from enum import Enum
from datetime import datetime, date


class ReportType(str, Enum):
    Daily = "daily"
    Weekly = "weekly"
    Monthly = "monthly"
    Yearly = "yearly"


class ReportStatus(str, Enum):
    SUCCESS = "success"
    FAIL = "fail"


class GetReportType(BaseModel):
    report_type: ReportType
    start_date: date | None = None
    end_date: date | None = None


class SaleReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    report_id: int
    report_type: ReportType
    report_start: datetime
    report_end: datetime
    metrics: dict
    comparison: dict
    report_status: ReportStatus
    generated_at: datetime
