from pydantic import BaseModel
from enum import Enum


class AuditStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class AuditContext(BaseModel):
    ip: str | None = None
    user_agent: str | None = None
