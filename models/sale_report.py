from database.connect import Base
from sqlalchemy import Integer, Enum as SqlEnum, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from enum import Enum
from datetime import datetime
from schemas.sale_report import ReportType, ReportStatus


class SaleReport(Base):
    __tablename__ = "sale_reports"

    report_id: Mapped[int] = mapped_column(
        Integer, primary_key=True, autoincrement=True)
    report_type: Mapped[Enum] = mapped_column(
        SqlEnum(ReportType), nullable=False)
    report_start: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    report_end: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False)
    comparison: Mapped[dict] = mapped_column(JSON, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
