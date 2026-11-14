from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, UTC
from models.audit_log import AuditLogs, AuditStatus
from fastapi import Request
from schemas.audit import AuditContext


async def create_audit_log(db: AsyncSession, audit: AuditContext, user_id: int | None,  entity_id: int | None, entity_type: str, event: str, old_value: dict | None, new_value: dict | None, status: AuditStatus = AuditStatus.SUCCESS):
    new_audit = AuditLogs(
        user_id=user_id,
        ip=audit.ip,
        user_agent=audit.user_agent,
        entity_id=entity_id,
        entity_type=entity_type,
        event=event,
        old_value=old_value,
        new_value=new_value,
        status=status,
        time=datetime.now(UTC)
    )

    db.add(new_audit)
    return new_audit


def create_audit_context(request: Request):
    return AuditContext(
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent")
    )
