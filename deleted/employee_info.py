from fastapi import HTTPException
from models.employee_info import EmployeeInfo
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc
from models.people import Person
from schemas.people import Roles, FullPersonInfo
from schemas.employee_info import EmployeeInfoUpdate, FilterEmployeeInfo, GetEmployeeInfo
import logging
from schemas.audit import AuditContext, AuditStatus
from crud.audit_log import create_audit_log
from schemas.wallet import SortOrder
from math import ceil

logger = logging.getLogger(__name__)


async def get_all_employees(audit: AuditContext, filter_employee_info: FilterEmployeeInfo, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="employee",
            event="EMPLOYEES_READ",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail='Not authorized for getting info about employees.')

    filters = []
    if filter_employee_info.employee_id is not None:
        filters.append(EmployeeInfo.employee_id ==
                       filter_employee_info.employee_id)
    if filter_employee_info.job_title is not None:
        filters.append(func.lower(EmployeeInfo.job_title) ==
                       filter_employee_info.job_title.lower())
    if filter_employee_info.min_salary is not None:
        filters.append(EmployeeInfo.salary >= filter_employee_info.min_salary)
    if filter_employee_info.max_salary is not None:
        filters.append(EmployeeInfo.salary <= filter_employee_info.max_salary)

    query = select(EmployeeInfo).where(*filters)
    result = select(func.count()).select_from(query.subquery())
    total = await db.scalar(result)
    offset = (filter_employee_info.page - 1)*filter_employee_info.page_size

    if filter_employee_info.sort_order == SortOrder.ASC:
        query = query.order_by(asc(filter_employee_info.sort_by)).offset(
            offset).limit(filter_employee_info.page_size)

    elif filter_employee_info.sort_order == SortOrder.DES:
        query = query.order_by(desc(filter_employee_info.sort_by)).offset(
            offset).limit(filter_employee_info.page_size)

    result = await db.execute(query)
    employees = result.scalars().all()

    if not employees:
        raise HTTPException(status_code=404, detail='No employee added yet')

    return GetEmployeeInfo(employees=employees, page=filter_employee_info.page, page_size=filter_employee_info.page_size, total=total, pages=ceil(total/filter_employee_info.page_size))


async def update_employee_info(employee: EmployeeInfoUpdate, audit: AuditContext, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=employee.employee_id,
            entity_type="employee",
            event="EMPLOYEE_UPDATED",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(EmployeeInfo).where(EmployeeInfo.employee_id == employee.employee_id))

    searched_employee_info = result.scalar_one_or_none()

    if searched_employee_info is None:
        raise HTTPException(
            status_code=404, detail=f"Employee {employee.employee_id} is not found.")

    try:
        update_data = employee.model_dump(exclude_unset=True)

        old_value = dict()
        new_value = dict()
        for key, value in update_data.items():
            old_value[key] = getattr(searched_employee_info, key)
            new_value[key] = value
            setattr(searched_employee_info, key, value)

        if "salary" in new_value.keys():
            old_value["salary"] = str(old_value["salary"])
            new_value["salary"] = str(new_value["salary"])

        result = await db.execute(select(Person).where(Person.user_id == employee.employee_id))
        searched_employee = result.scalar_one_or_none()

        if searched_employee is None:
            raise HTTPException(
                status_code=404, detail=f"Employee {employee.employee_id} not found")

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=employee.employee_id,
            entity_type="employee",
            event="EMPLOYEE_UPDATE",
            old_value=old_value,
            new_value=new_value
        )

        await db.commit()
        await db.refresh(searched_employee_info)

        return FullPersonInfo(person=searched_employee, employee_info=searched_employee_info)

    except Exception:
        logger.exception(f"Update employee info {employee.employee_id} failed")
        raise
