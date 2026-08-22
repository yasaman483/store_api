from fastapi import HTTPException
from models.employee_info import EmployeeInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.people import Person
from schemas.people import Roles
from schemas.employee_info import GetEmployeeId, EmployeeInfoUpdate
from datetime import datetime, UTC
import logging

logger = logging.getLogger(__name__)


async def get_all_employees(current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER:
        error = {
            "event": "Get all employees' info failed",
            "method": "POST",
            "error": "Not authorized to get all employees' info.",
            "path": "/employees_info/get_employees",
            "user_id": current_user.user_id,
            "status_code": 403
        }
        logger.error(error)
        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')

    result = await db.execute(select(EmployeeInfo))

    employees = result.scalars().all()

    if not employees:
        raise HTTPException(status_code=404, detail='No employees added yet')

    end_time = datetime.now(UTC)
    info = {
        "event": "Get all employess' info succeeded",
        "method": "POST",
        "path": "/employees_info/get_employees",
        "user_id": current_user.user_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return employees


async def get_employee_by_id(employee: GetEmployeeId, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER:
        error = {
            "event": "Get employee info by id failed",
            "method": "POST",
            "error": "Not authorized to get employee info by id.",
            "path": "/employees_info/get_employee_by_id",
            "employee_id": employee.employee_id,
            "user_id": current_user.user_id,
            "status_code": 403
        }
        logger.error(error)

        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')

    result = await db.execute(select(EmployeeInfo).where(
        EmployeeInfo.employee_id == employee.employee_id))

    searched_employee = result.scalar_one_or_none()

    if not searched_employee:
        raise HTTPException(
            status_code=404, detail=f"Employee {employee.employee_id} not found")

    end_time = datetime.now(UTC)
    info = {
        "event": "Get employee info by id succeeded",
        "method": "POST",
        "path": "/employees_info/get_employee_by_id",
        "employee_id": searched_employee.employee_id,
        "user_id": current_user.user_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return searched_employee


async def update_employee_info(employee: EmployeeInfoUpdate, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER:
        error = {
            "event": "Update employee info by id failed",
            "method": "POST",
            "error": "Not authorized to get employee info by id.",
            "path": "/employees_info/update_employee_info",
            "employee_id": employee.employee_id,
            "user_id": current_user.user_id,
            "status_code": 403
        }
        logger.error(error)

        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(EmployeeInfo).where(EmployeeInfo.employee_id == employee.employee_id))

    searched_employee = result.scalar_one_or_none()

    if searched_employee is None:
        raise HTTPException(
            status_code=404, detail=f"Employee {employee.employee_id} is not found.")

    update_data = employee.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(searched_employee, key, value)

    await db.commit()
    await db.refresh(searched_employee)

    end_time = datetime.now(UTC)
    info = {
        "event": "Update employee info by id succeeded",
        "method": "POST",
        "path": "/employees_info/update_employee_info",
        "employee_id": searched_employee.employee_id,
        "user_id": current_user.user_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return searched_employee
