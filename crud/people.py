from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.people import Person
from models.employee_info import EmployeeInfo
from schemas.people import PersonCreate, LoginRequest, LoginResponse, GetId, PersonUpdate
import auth
from datetime import datetime, timedelta, UTC
from config import setting
from schemas.people import Roles
from schemas.employee_info import EmployeeStatus
from models.wallet import Wallet
import logging

logger = logging.getLogger(__name__)


async def sign_up(person: PersonCreate, db: AsyncSession, current_user: Person | None = None):
    try:
        start_time = datetime.now(UTC)
        if current_user and current_user.role == Roles.MANAGER:
            if person.report_to:
                new_employee = Person(
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

                new_report_to = EmployeeInfo(
                    employee_id=new_employee.user_id,
                    job_title=person.report_to.job_title,
                    salary=person.report_to.salary,
                    employee_status=EmployeeStatus.ACTIVE
                )

                end_time = datetime.now(UTC)
                duration = (end_time - start_time).total_seconds()

                db.add(new_report_to)
                await db.commit()
                await db.refresh(new_employee)

                info = {
                    "event": "New employee added successfully",
                    "methood": "POST",
                    "path": "/people/sign_up",
                    "manager_id": current_user.user_id,
                    "added_user_id": new_employee.user_id,
                    "status_code": 200,
                    "duration_s": duration
                }
                logger.info(info)
                return new_employee

        if current_user:
            raise HTTPException(
                status_code=403, detail="Not authorized to add employee")

        if current_user is None and person.report_to:
            raise HTTPException(
                status_code=403, detail="Not authorized to add employee")

        new_customer = Person(
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
            customer_id=new_customer.user_id
        )
        db.add(new_wallet)

        await db.commit()
        await db.refresh(new_customer)

        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()
        info = {
            "event": "New customer added successfully",
            "methood": "POST",
            "path": "/people/sign_up",
            "added_user_id": new_customer.user_id,
            "added_wallet_id": new_wallet.wallet_id,
            "status_code": 200,
            "duration_s": duration
        }
        logger.info(info)
        return new_customer

    except Exception as ex:
        end_time = datetime.now(UTC)
        duration = (end_time - start_time).total_seconds()
        error = {
            "event": "New user didn't add successfully",
            "error": ex,
            "methood": "POST",
            "path": "/people/sign_up",
            "duration_s": duration
        }
        logger.info(error)
        await db.rollback()
        raise ex


async def login_for_access_token(login_data: LoginRequest, db: AsyncSession):
    start_time = datetime.now(UTC)
    result = await db.execute(select(Person).where(
        Person.phone == login_data.phone))

    user = result.scalar_one_or_none()

    if user is None or not auth.verify_password(login_data.password, user.password_hash):
        end_time = datetime.now(UTC)
        error = {
            "event": "Login failed",
            "method": "POST",
            "error": "User not found or verification failed",
            "path": "/people/login",
            "user_phone": login_data.phone,
            "status_code": 404,
            "duration_s": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        raise HTTPException(
            status_code=404, detail=f'Incorrect phone number or password')

    access_token_expire = timedelta(
        minutes=setting.access_token_expire_minutes)
    access_token = auth.create_access_token(
        {"sub": str(user.user_id)}, access_token_expire)

    end_time = datetime.now(UTC)
    info = {
        "event": "Login succeeded",
        "method": "POST",
        "path": "/people/login",
        "user_phone": login_data.phone,
        "status_code": 200,
        "duration_s": (end_time - start_time).total_seconds()
    }
    logger.error(info)
    return LoginResponse(access_token=access_token, token_type="bearer", user=user)


async def get_current_user(credentials: HTTPAuthorizationCredentials, db: AsyncSession):
    start_time = datetime.now(UTC)
    token = credentials.credentials
    user_id = auth.verify_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token.")

    try:
        user_id_int = int(user_id)
    except:
        end_time = datetime.now(UTC)
        error = {
            "event": "Current user info didn't send successfully",
            "method": "POST",
            "error": "Something wrong happend with the token",
            "path": "/people/me",
            "user_id": user_id_int,
            "status_code": 401,
            "duration_s": (end_time - start_time).total_seconds()
        }
        logger.error(error)
        raise HTTPException(status_code=401, detail='Invalid or expired token')

    result = await db.execute(select(Person).where(Person.user_id == user_id_int))

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404, detail=f'User {user_id} not found.')

    end_time = datetime.now(UTC)
    info = {
        "event": "Current user info sendt successfully",
        "method": "POST",
        "path": "/people/me",
        "user_id": user_id_int,
        "status_code": 200,
        "duration_s": (end_time - start_time).total_seconds()
    }
    logger.error(info)
    return user


async def get_all_people_info(current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER:
        error = {
            "event": "Sent all people info failed",
            "method": "POST",
            "error": "User doesn't have permission to get users' info",
            "psth": "/people/get_all_people_info",
            "user_id": current_user.user_id,
            "status_code": 403
        }
        logger.error(error)
        raise HTTPException(
            status_code=403, detail=f"Not authorized to get users' info.")

    result = await db.execute(select(Person))

    users = result.scalars().all()

    if not users:
        HTTPException(status_code=404, detail='No user added yet')

    end_time = datetime.now(UTC)
    info = {
        "event": "All people info sent successfully",
        "method": "POST",
        "psth": "/people/get_all_people_info",
        "user_id": current_user.user_id,
        "status_code": 200,
        "duration_s": (end_time - start_time).total_seconds()
    }
    logger.info(info)
    return users


async def get_person_by_id(person: GetId, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER:
        error = {
            "event": "Sent person info failed",
            "method": "POST",
            "error": "User doesn't have permission to get user info",
            "psth": "/people/get_person_info_by_id",
            "user_id": current_user.user_id,
            "status_code": 403
        }
        logger.error(error)
        raise HTTPException(status_code=403, detail="Not authorized")

    result = await db.execute(select(Person).where(
        Person.user_id == person.user_id))

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User {person.user_id} not found")

    end_time = datetime.now(UTC)
    info = {
        "event": "Person info sent successfully",
        "method": "POST",
        "psth": "/people/get_person_info_by_id",
        "user_id": current_user.user_id,
        "status_code": 200,
        "duration_s": (end_time - start_time).total_seconds()
    }
    logger.info(info)
    return user


async def update_info(person: PersonUpdate, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if person.user_id == None:
        user_id = current_user.user_id

    else:
        if current_user.role != Roles.MANAGER:
            end_time = datetime.now(UTC)
            error = {
                "event": "Update person info failed",
                "method": "POST",
                "error": "User doesn't have permission to update user info",
                "path": "/people/edit_info",
                "user_id": current_user.user_id,
                "status_code": 403,
                "duration": (end_time - start_time).total_seconds()
            }
            logger.error(error)
            raise HTTPException(status_code=403, detail="Not authorized")
        user_id = person.user_id

    result = await db.execute(select(Person).where(
        Person.user_id == user_id))

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail='Person Not Found.')

    try:
        update_data = person.model_dump(exclude_unset=True)

        if user.role == "employee" and "report_to" in update_data.keys():
            employee_report_info = update_data.pop("report_to")

            result = await db.execute(select(EmployeeInfo).where(EmployeeInfo.employee_id == person.user_id))

            employee = result.scalar_one_or_none()

            for key, value in employee_report_info.items():
                setattr(employee, key, value)

        if user.role != "employee" and "report_to" in update_data.keys():
            raise HTTPException(
                status_code=403, detail="Report To is not an info for all users except employees")

        if "password" in update_data:
            update_data["password_hash"] = auth.hash_password(
                update_data.pop("password"))

        for key, value in update_data.items():
            setattr(user, key, value)

        await db.commit()
        await db.refresh(user)

        end_time = datetime.now(UTC)
        info = {
            "event": "Update person info succeeded",
            "method": "POST",
            "path": "/people/edit_info",
            "updater_user_id": current_user.user_id,
            "updated_user_id": person.user_id,
            "status_code": 200,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.info(info)

        return user

    except Exception as ex:
        end_time = datetime.now(UTC)
        error = {
            "event": "Update person info failed",
            "method": "POST",
            "error": f"{ex}",
            "path": "/people/edit_info",
            "user_id": current_user.user_id,
            "duration": (end_time - start_time).total_seconds()
        }
        logger.error(error)

        await db.rollback()
        raise ex


async def delete_person_info(person_info: GetId, current_user: Person, db: AsyncSession):
    start_time = datetime.now(UTC)
    if current_user.role != Roles.MANAGER:
        error = {
            "event": "Delete person info failed",
            "method": "POST",
            "error": 'Not authorized to get all people info',
            "path": "/people/delete_person_info",
            "user_id": current_user.user_id,
            "status_code": 403
        }
        logger.error(error)

        raise HTTPException(
            status_code=403, detail=f'Not authorized to get all people info.')

    result = await db.execute(select(Person).where(
        Person.user_id == person_info.user_id))

    searched_person = result.scalar_one_or_none()

    if searched_person is None:
        raise HTTPException(status_code=404, detail='Person Not Found')

    await db.delete(searched_person)
    await db.commit()

    end_time = datetime.now(UTC)
    info = {
        "event": "Delete person info succeeded",
        "method": "POST",
        "path": "/people/delete_person_info",
        "deleter_user_id": current_user.user_id,
        "deleted_user_id": person_info.user_id,
        "status_code": 200,
        "duration": (end_time - start_time).total_seconds()
    }
    logger.info(info)

    return {"message": "Person deleted successfully."}
