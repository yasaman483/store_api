from sqlalchemy import String, Integer, DateTime, BigInteger, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column
from database.connect import Base
from sqlalchemy.dialects.mysql import JSON
from datetime import datetime, UTC
from schemas.audit import AuditStatus


class AuditLogs(Base):
    __tablename__ = "audit_logs"

    audit_id: Mapped[int | None] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ip: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    event: Mapped[str] = mapped_column(String(100), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(SQLEnum(AuditStatus), nullable=False)
    time: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC))
