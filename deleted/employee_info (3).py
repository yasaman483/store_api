from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from schemas.employee_info import EmployeeInfoResponse, EmployeeInfoUpdate, FilterEmployeeInfo, GetEmployeeInfo, FullPersonInfo
from crud.employee_info import get_all_employees, update_employee_info
from models.people import Person
import auth
from crud.audit_log import create_audit_context

router = APIRouter(prefix='/employees_info', tags=['EmployeesInfo'])


@router.post('/get_employees', response_model=GetEmployeeInfo)
async def read_all_employees(request: Request, filter_employee_info: FilterEmployeeInfo, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await get_all_employees(audit, filter_employee_info, current_user, db)


@router.patch('/update_employee_info', response_model=FullPersonInfo)
async def edit_employee_info(employee: EmployeeInfoUpdate, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await update_employee_info(employee, audit, current_user, db)
