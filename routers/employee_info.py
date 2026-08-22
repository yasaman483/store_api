from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from schemas.employee_info import EmployeeInfoResponse, GetEmployeeId, EmployeeInfoUpdate
from crud.employee_info import get_all_employees, get_employee_by_id, update_employee_info
from models.people import Person
import auth

router = APIRouter(prefix='/employees_info', tags=['EmployeesInfo'])


@router.post('/get_employees', response_model=list[EmployeeInfoResponse])
async def read_all_employees(current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_all_employees(current_user, db)


@router.post('/get_employee_by_id', response_model=EmployeeInfoResponse)
async def read_employee_by_id(employee: GetEmployeeId, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_employee_by_id(employee, current_user, db)


@router.put('/update_employee_info', response_model=EmployeeInfoResponse)
async def edit_employee_info(employee: EmployeeInfoUpdate, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_employee_info(employee, current_user, db)
