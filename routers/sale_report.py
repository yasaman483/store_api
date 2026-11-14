from fastapi import APIRouter, Request, Depends
from database.connect import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from crud.people import Person
from crud.sale_report import get_report
from auth import get_current_user
from schemas.sale_report import GetReportType, SaleReportResponse
from crud.audit_log import create_audit_context


router = APIRouter(prefix='/sale_report', tags=['SaleReport'])


@router.post('/report', response_model=SaleReportResponse)
async def read_report(report: GetReportType, request: Request, current_user: Person = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await get_report(report, audit, current_user, db)
