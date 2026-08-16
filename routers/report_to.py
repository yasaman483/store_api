from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from schemas.report_to import ReportToResponse, GetEmployeeId, ReportToUpdate
from crud.report_to import get_all_employees, get_employee_by_id, update_employee_info
from models.people import People
import auth

router = APIRouter(prefix='/report_to', tags=['ReportTo'])


@router.post('/get_employees', response_model=list[ReportToResponse])
async def read_all_employees(current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_all_employees(current_user, db)


@router.post('/get_employee_by_id', response_model=ReportToResponse)
async def read_employee_by_id(employee: GetEmployeeId, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_employee_by_id(employee, current_user, db)


@router.put('/update_employee_info', response_model=ReportToResponse)
async def edit_employee_info(employee: ReportToUpdate, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_employee_info(employee, current_user, db)
