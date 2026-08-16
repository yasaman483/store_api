from fastapi import HTTPException
from models.report_to import ReportTo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.people import People
from schemas.people import Roles
from schemas.report_to import GetEmployeeId, ReportToUpdate


async def get_all_employees(current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER:
        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')

    result = await db.execute(select(ReportTo))

    employees = result.scalars().all()

    if not employees:
        raise HTTPException(status_code=404, detail='No employees added yet')

    return employees


async def get_employee_by_id(employee: GetEmployeeId, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER:
        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')

    result = await db.execute(select(ReportTo).where(
        ReportTo.employee_id == employee.employee_id))

    searched_employee = result.scalar_one_or_none()

    if not searched_employee:
        raise HTTPException(
            status_code=404, detail=f"Employee {employee.employee_id} not found")

    return searched_employee


async def update_employee_info(employee: ReportToUpdate, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(ReportTo).where(ReportTo.employee_id == employee.employee_id))

    searched_employee = result.scalar_one_or_none()

    if searched_employee is None:
        raise HTTPException(
            status_code=404, detail=f"Employee {employee.employee_id} is not found.")

    update_data = employee.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        setattr(searched_employee, key, value)

    await db.commit()
    await db.refresh(searched_employee)
    return searched_employee
