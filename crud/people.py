from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.people import People
from models.report_to import ReportTo
from schemas.people import PeopleCreate, LoginRequest, LoginResponse, GetId, PeopleUpdate
import auth
from datetime import timedelta
from config import setting
from schemas.people import Roles
from schemas.report_to import EmployeeStatus
from models.wallet import Wallet


async def sign_up(person: PeopleCreate, db: AsyncSession, current_user: People | None = None):
    try:
        if current_user and current_user.role == Roles.MANAGER:
            if person.report_to:
                new_employee = People(
                    first_name=person.first_name,
                    last_name=person.last_name,
                    password_hash=auth.hash_password(person.password),
                    birth_date=person.birth_date,
                    phone=person.phone,
                    address=person.address,
                    city=person.city,
                    role=Roles.EMPLOYEE
                )

                db.add(new_employee)
                await db.flush()

                new_report_to = ReportTo(
                    employee_id=new_employee.people_id,
                    job_title=person.report_to.job_title,
                    salary=person.report_to.salary,
                    employee_status=EmployeeStatus.ACTIVE
                )

                db.add(new_report_to)
                await db.commit()
                await db.refresh(new_employee)
                return new_employee

        if current_user:
            raise HTTPException(
                status_code=403, detail="Not authorized to add employee")

        if current_user is None and person.report_to:
            raise HTTPException(
                status_code=403, detail="Not authorized to add employee")

        new_customer = People(
            first_name=person.first_name,
            last_name=person.last_name,
            password_hash=auth.hash_password(person.password),
            birth_date=person.birth_date,
            phone=person.phone,
            address=person.address,
            city=person.city,
            role=Roles.CUSTOMER
        )

        db.add(new_customer)
        await db.flush()

        new_wallet = Wallet(
            customer_id=new_customer.people_id
        )
        db.add(new_wallet)

        await db.commit()
        await db.refresh(new_customer)
        return new_customer

    except Exception as ex:
        await db.rollback()
        raise ex


async def login_for_access_token(login_data: LoginRequest, db: AsyncSession):
    result = await db.execute(select(People).where(
        People.phone == login_data.phone))

    user = result.scalar_one_or_none()

    if user is None or not auth.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=404, detail=f'Incorrect phone number or password')

    access_token_expire = timedelta(
        minutes=setting.access_token_expire_minutes)
    access_token = auth.create_access_token(
        {"sub": str(user.people_id)}, access_token_expire)

    return LoginResponse(access_token=access_token, token_type="bearer", user=user)


async def get_current_user(credentials: HTTPAuthorizationCredentials, db: AsyncSession):
    token = credentials.credentials
    user_id = auth.verify_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token.")

    try:
        user_id_int = int(user_id)
    except:
        raise HTTPException(status_code=401, detail='Invalid or expired token')

    result = await db.execute(select(People).where(People.people_id == user_id_int))

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404, detail=f'User {user_id} not found.')

    return user


async def get_all_people_info(current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER:
        raise HTTPException(
            status_code=403, detail=f'Not authorized to get all people info.')

    result = await db.execute(select(People))

    users = result.scalars().all()

    if not users:
        HTTPException(status_code=404, detail='No people added yet')

    return users


async def get_people_by_id(person: GetId, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER:
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(People).where(
        People.people_id == person.people_id))

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User {person.people_id} not found")

    return user


async def update_info(person: PeopleUpdate, current_user: People, db: AsyncSession):
    if person.people_id == None:
        user_id = current_user.people_id

    else:
        if current_user.role != Roles.MANAGER:
            raise HTTPException(status_code=403, detail="Not authorized")
        user_id = person.people_id

    result = await db.execute(select(People).where(
        People.people_id == user_id))

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail='Person Not Found.')

    try:
        update_data = person.model_dump(exclude_unset=True)

        if user.role == "employee" and "report_to" in update_data.keys():
            employee_report_info = update_data.pop("report_to")

            result = await db.execute(select(ReportTo).where(ReportTo.employee_id == person.people_id))

            employee = result.scalar_one_or_none()

            for key, value in employee_report_info.items():
                setattr(employee, key, value)

        if user.role != "employee" and "report_to" in update_data.keys():
            raise HTTPException(
                status_code=403, detail="Report To is not an info for people except employees")

        if "password" in update_data:
            update_data["password_hash"] = auth.hash_password(
                update_data.pop("password"))

        for key, value in update_data.items():
            setattr(user, key, value)

        await db.commit()
        await db.refresh(user)
        return user

    except Exception as ex:
        await db.rollback()
        raise ex


async def delete_person_info(person_info: GetId, current_user: People, db: AsyncSession):
    if current_user.role != Roles.MANAGER:
        raise HTTPException(
            status_code=403, detail=f'Not authorized to get all people info.')

    result = await db.execute(select(People).where(
        People.phone == person_info.people_id))

    searched_person = result.scalar_one_or_none()

    if searched_person is None:
        raise HTTPException(status_code=404, detail='Person Not Found')

    await db.delete(searched_person)
    await db.commit()
    return {"message": "Person deleted successfully."}


# async def sign_up(person: CustomerCreate, db: AsyncSession):
#     try:
#         new_customer = People(
#             first_name=person.first_name,
#             last_name=person.last_name,
#             password_hash=auth.hash_password(person.password),
#             birth_date=person.birth_date,
#             phone=person.phone,
#             address=person.address,
#             city=person.city,
#             role=Roles.CUSTOMER
#         )
#         db.add(new_customer)
#         await db.flush()

#         new_wallet = Wallet(
#             customer_id=new_customer.people_id
#         )
#         db.add(new_wallet)

#         await db.commit()
#         await db.refresh(new_customer)
#         return new_customer

#     except Exception as ex:
#         await db.rollback()
#         raise ex

# async def update_person_info(person: CustomerUpdate, current_user: People, db: AsyncSession):
#     result = await db.execute(select(People).where(
#         People.people_id == current_user.people_id))

#     user = result.scalar_one_or_none()

#     if user is None:
#         raise HTTPException(status_code=404, detail='Person Not Found.')

#     try:
#         update_data = person.model_dump(exclude_unset=True)

#         if "password" in update_data:
#             update_data["password_hash"] = auth.hash_password(
#                 update_data.pop("password"))

#         for key, value in update_data.items():
#             setattr(user, key, value)

#         await db.commit()
#         await db.refresh(user)
#         return user

#     except Exception as ex:
#         await db.rollback()
#         raise ex


# async def update_employee_info(current_info: EmployeeUpdateGet, person: EmployeeUpdateSent, current_user: People, db: AsyncSession):
#     if current_user.role != Roles.MANAGER:
#         raise HTTPException(
#             status_code=403, detail='Not authorized to edit employee info')

#     result = await db.execute(select(People).where(
#         People.phone == current_info.phone))

#     user = result.scalar_one_or_none()

#     if user is None:
#         raise HTTPException(status_code=404, detail="Employee not found")

#     if user.role != Roles.EMPLOYEE:
#         raise HTTPException(
#             status_code=403, detail=f'Not authorized to edit info for user with phone {user.phone}')

#     try:
#         update_data = person.model_dump(exclude_unset=True)

#         if "password" in update_data.keys():
#             update_data["password_hash"] = auth.hash_password(
#                 update_data.pop("password"))

#         if "report_to" in update_data.keys():
#             report_data = update_data.pop("report_to")

#             result = await db.execute(select(ReportTo).where(
#                 ReportTo.employee_id == user.people_id))

#             employee_reports = result.scalar_one_or_none()

#             for key, value in report_data.items():
#                 setattr(employee_reports, key, value)

#             await db.flush()

#         for key, value in update_data.items():
#             setattr(user, key, value)

#         await db.commit()
#         await db.refresh(user)
#         return user

#     except Exception as e:
#         await db.rollback()
#         print(e)

# async def add_employee(person: EmployeeCreate, current_user: People, db: AsyncSession):
#     try:
#         if current_user.role != Roles.MANAGER:
#             raise HTTPException(
#                 status_code=403, detail='Not authorized for adding emplyee.')

#         new_employee = People(
#             first_name=person.first_name,
#             last_name=person.last_name,
#             password_hash=auth.hash_password(person.password),
#             birth_date=person.birth_date,
#             phone=person.phone,
#             address=person.address,
#             city=person.city,
#             role=Roles.EMPLOYEE
#         )

#         db.add(new_employee)
#         await db.flush()

#         new_report_to = ReportTo(
#             employee_id=new_employee.people_id,
#             job_title=person.report_to.job_title,
#             salary=person.report_to.salary,
#             employee_status=EmployeeStatus.ACTIVE
#         )

#         db.add(new_report_to)
#         await db.commit()
#         await db.refresh(new_employee)
#         return new_employee

#     except Exception as ex:
#         await db.rollback()
#         raise ex

# async def get_people_by_phone(person: GetPhone, current_user: People, db: AsyncSession):
#     if current_user.role != Roles.MANAGER:
#         raise HTTPException(status_code=403, detail="Not authorized")

#     result = await db.execute(select(People).where(People.phone == person.phone))

#     user = result.scalar_one_or_none()

#     if user is None:
#         raise HTTPException(
#             status_code=404, detail=f"User with phone number {person.phone} not found")

#     return user
