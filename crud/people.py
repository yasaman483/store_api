from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc
from sqlalchemy.exc import IntegrityError
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import selectinload
from models.people import Person
from models.employee_info import EmployeeInfo
from schemas.people import PersonCreate, LoginRequest, LoginResponse, GetId, PersonUpdate, Roles, FullPersonInfo, FilterPeople, GetPeopleInfo
import auth
from datetime import timedelta
from config import setting
from schemas.people import PersonStatus
from models.caret import Caret
from models.wallet import Wallet
from crud.wallet import make_json_format
from schemas.wallet import SortOrder
import logging
from crud.audit_log import create_audit_log
from schemas.audit import AuditStatus, AuditContext
from math import ceil

logger = logging.getLogger(__name__)


async def sign_up(person: PersonCreate, audit: AuditContext, db: AsyncSession, current_user: Person | None):
    try:
        new_value = dict()
        if current_user and current_user.role == Roles.MANAGER:
            if person.employee_info:
                new_employee = Person(
                    first_name=person.first_name,
                    last_name=person.last_name,
                    password_hash=auth.hash_password(person.password),
                    birth_date=person.birth_date,
                    phone=person.phone,
                    address=person.address,
                    city=person.city,
                    role=Roles.EMPLOYEE,
                    person_status=person.person_status if person.person_status else PersonStatus.ACTIVE
                )

                db.add(new_employee)
                await db.flush()

                new_employee_info = EmployeeInfo(
                    employee_id=new_employee.user_id,
                    job_title=person.employee_info.job_title,
                    salary=person.employee_info.salary
                )

                db.add(new_employee_info)
                await db.flush()

                new_value.update(**{column.key: getattr(new_employee, column.key) for column in inspect(Person).mapper.column_attrs},
                                 **{column.key: getattr(new_employee_info, column.key) for column in inspect(EmployeeInfo).mapper.column_attrs})

                new_value = make_json_format(new_value)

                await create_audit_log(
                    db=db,
                    audit=audit,
                    user_id=current_user.user_id,
                    entity_id=new_employee.user_id,
                    entity_type="person",
                    event="EMPLOYEE_CREATED",
                    old_value=None,
                    new_value=new_value
                )

                await db.commit()
                await db.refresh(new_employee)
                return FullPersonInfo(person=new_employee, employee_info=new_employee_info)

        elif current_user and current_user.role != Roles.EMPLOYEE:
            await create_audit_log(
                db=db,
                audit=audit,
                user_id=current_user.user_id,
                entity_id=None,
                entity_type="person",
                event="CUSTOMER_CREATED",
                old_value=None,
                new_value=None,
                status=AuditStatus.FAILED
            )
            await db.commit()

            raise HTTPException(
                status_code=403, detail="Not authorized to add others")

        elif current_user and current_user.role == Roles.EMPLOYEE and person.employee_info:
            await create_audit_log(
                db=db,
                audit=audit,
                user_id=current_user.user_id,
                entity_id=None,
                entity_type="person",
                event="EMPLOYEE_CREATED",
                old_value=None,
                new_value=None,
                status=AuditStatus.FAILED
            )
            await db.commit()

            raise HTTPException(
                status_code=403, detail="Not authorized to add employee")

        elif current_user is None and person.employee_info:
            raise HTTPException(
                status_code=403, detail="Not allowed to add employee")

        new_customer = Person(
            first_name=person.first_name,
            last_name=person.last_name,
            password_hash=auth.hash_password(person.password),
            birth_date=person.birth_date,
            phone=person.phone,
            address=person.address,
            city=person.city,
            role=Roles.CUSTOMER,
            person_status=person.person_status if person.person_status else PersonStatus.ACTIVE
        )

        db.add(new_customer)
        await db.flush()

        new_wallet = Wallet(
            customer_id=new_customer.user_id
        )
        db.add(new_wallet)
        await db.flush()

        new_caret = Caret(
            user_id=new_customer.user_id
        )
        db.add(new_caret)
        await db.flush()

        new_value.update({**{column.key: getattr(new_customer, column.key) for column in inspect(Person).mapper.column_attrs},
                          **{column.key: getattr(new_wallet, column.key) for column in inspect(Wallet).mapper.column_attrs},
                          **{column.key: getattr(new_caret, column.key) for column in inspect(Caret).mapper.column_attrs}})

        new_value = make_json_format(new_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id if current_user else None,
            entity_id=new_customer.user_id,
            entity_type="person",
            event="CUSTOMER_CREATED",
            old_value=None,
            new_value=new_value
        )
        await db.commit()
        await db.refresh(new_customer)
        return FullPersonInfo(person=new_customer, employee_info=None)

    except HTTPException:
        await db.rollback()
        raise

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Confliction happend")

    except Exception:
        logger.exception("New user didn't add successfully")

        await db.rollback()
        raise


async def login_for_access_token(login_data: LoginRequest, audit: AuditContext, db: AsyncSession):
    result = await db.execute(select(Person).where(
        Person.phone == login_data.phone))

    user = result.scalar_one_or_none()

    if user is None or not auth.verify_password(login_data.password, user.password_hash):
        logger.warning(
            f"User not found or verification failed")
        raise HTTPException(
            status_code=401, detail='Incorrect phone number or password')

    if user.person_status == PersonStatus.UNACTIVE:
        raise HTTPException(
            status_code=403, detail="The account is unactivated")

    access_token_expire = timedelta(
        minutes=setting.access_token_expire_minutes)

    access_token = auth.create_access_token(
        {"sub": str(user.user_id)}, access_token_expire)

    await create_audit_log(
        db=db,
        audit=audit,
        user_id=user.user_id,
        entity_id=None,
        entity_type="person",
        event="LOGIN",
        old_value=None,
        new_value=None
    )
    await db.commit()

    return LoginResponse(access_token=access_token, token_type="bearer", user=user)


async def me(credentials: HTTPAuthorizationCredentials | None, db: AsyncSession):
    if credentials is None:
        raise HTTPException(status_code=403, detail="Not authorized")

    token = credentials.credentials
    user_id = auth.verify_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401, detail="Invalid or expired token.")

    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        logger.exception(
            f"Current user info with user id {user_id} didn't send successfully")
        raise HTTPException(status_code=401, detail='Invalid or expired token')

    result = await db.execute(select(Person).where(Person.user_id == user_id_int))

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=404, detail=f'User {user_id} not found.')

    if user.person_status == PersonStatus.UNACTIVE:
        raise HTTPException(
            status_code=403, detail="The account is unactivated")

    return user


async def get_all_people_info(audit: AuditContext, filter_people: FilterPeople, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=None,
            entity_type="person",
            event="PEOPLE_READ",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail=f"Not authorized to get users' info.")

    filters = []
    if filter_people.user_id is not None:
        filters.append(Person.user_id == filter_people.user_id)
    if filter_people.role is not None:
        filters.append(Person.role == filter_people.role)
    if filter_people.first_name is not None:
        filters.append(func.lower(Person.first_name) ==
                       filter_people.first_name.lower())
    if filter_people.last_name is not None:
        filters.append(func.lower(Person.last_name) ==
                       filter_people.last_name.lower())
    if filter_people.before_date_birth_date is not None:
        filters.append(Person.birth_date <=
                       filter_people.before_date_birth_date)
    if filter_people.after_date_birth_date is not None:
        filters.append(Person.birth_date >=
                       filter_people.after_date_birth_date)
    if filter_people.phone is not None:
        filters.append(Person.phone == filter_people.phone)
    if filter_people.address is not None:
        filters.append(func.lower(Person.address) ==
                       filter_people.address.lower())
    if filter_people.city is not None:
        filters.append(func.lower(Person.city) == filter_people.city.lower())
    if filter_people.person_status is not None:
        filters.append(Person.person_status ==
                       filter_people.person_status.lower())
    if filter_people.job_title is not None and (filter_people.role == Roles.EMPLOYEE or filter_people.role is None):
        filters.append(Person.employee_info.has(
            func.lower(EmployeeInfo.job_title) == filter_people.job_title.lower()))
    if filter_people.min_salary is not None and (filter_people.role == Roles.EMPLOYEE or filter_people.role is None):
        filters.append(Person.employee_info.has(
            EmployeeInfo.salary >= filter_people.min_salary))
    if filter_people.max_salary is not None and (filter_people.role == Roles.EMPLOYEE or filter_people.role is None):
        filters.append(Person.employee_info.has(
            EmployeeInfo.salary <= filter_people.max_salary))

    query = select(Person).options(selectinload(
        Person.employee_info)).where(*filters)
    result = select(func.count()).select_from(query.subquery())
    total = await db.scalar(result)
    offset = (filter_people.page - 1)*filter_people.page_size

    if filter_people.sort_order == SortOrder.ASC:
        query = query.order_by(asc(filter_people.sort_by)).offset(
            offset).limit(filter_people.page_size)
    if filter_people.sort_order == SortOrder.DES:
        query = query.order_by(desc(filter_people.sort_by)).offset(
            offset).limit(filter_people.page_size)

    result = await db.execute(query)
    users = result.scalars().all()

    if not users:
        raise HTTPException(status_code=404, detail='No user added yet')

    response = []
    for user in users:
        if user.role == Roles.EMPLOYEE:
            response.append(FullPersonInfo(
                person=user, employee_info=user.employee_info))
        else:
            response.append(FullPersonInfo(person=user, employee_info=None))

    return GetPeopleInfo(people=response, page=filter_people.page, page_size=filter_people.page_size, total=total, pages=ceil(total/filter_people.page_size))


async def update_info(person: PersonUpdate, audit: AuditContext, current_user: Person, db: AsyncSession):
    if person.user_id == None:
        user_id = current_user.user_id

    else:
        if current_user.role != Roles.MANAGER:
            await create_audit_log(
                db=db,
                audit=audit,
                user_id=current_user.user_id,
                entity_id=person.user_id,
                entity_type="person",
                event="PEOPLE_UPDATED",
                old_value=None,
                new_value=None,
                status=AuditStatus.FAILED
            )
            raise HTTPException(status_code=403, detail="Not authorized")
        user_id = person.user_id

    result = await db.execute(select(Person).where(
        Person.user_id == user_id))

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=404, detail='Person Not Found.')

    if user.person_status == PersonStatus.UNACTIVE and person.person_status and person.person_status != PersonStatus.ACTIVE:
        raise HTTPException(
            status_code=403, detail="The account is unactivated")

    try:
        old_value = dict()
        new_value = dict()
        update_data = person.model_dump(exclude_unset=True)

        if current_user.role == Roles.EMPLOYEE and "employee_info" in update_data.keys():
            raise HTTPException(
                status_code=403, detail="Not allowed to change the special info")

        if user.role == Roles.EMPLOYEE and "employee_info" in update_data.keys():
            employee_info = update_data.pop("employee_info")

            result = await db.execute(select(EmployeeInfo).where(EmployeeInfo.employee_id == person.user_id))

            employee = result.scalar_one_or_none()

            if employee is None:
                raise HTTPException(
                    status_code=404, detail=f"Employee {person.user_id} not found")

            for key, value in employee_info.items():
                old_value[key] = getattr(employee, key)
                new_value[key] = value
                setattr(employee, key, value)

        if user.role != Roles.EMPLOYEE and "employee_info" in update_data.keys():
            raise HTTPException(
                status_code=403, detail="Employee info is not an info for all users except employees")

        if "password" in update_data:
            update_data["password_hash"] = auth.hash_password(
                update_data.pop("password"))

        for key, value in update_data.items():
            if key != "password_hash":
                old_value[key] = getattr(user, key)
                new_value[key] = value
            setattr(user, key, value)

        new_value = make_json_format(new_value)
        old_value = make_json_format(old_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=user_id,
            entity_type="person",
            event="PERSON_UPDATED",
            old_value=old_value,
            new_value=new_value
        )

        await db.commit()

        if user.role == Roles.MANAGER:
            await db.refresh(user)
            return FullPersonInfo(person=user, employee_info=None)
        else:
            await db.refresh(user, attribute_names=["employee_info"])
            return FullPersonInfo(person=user, employee_info=user.employee_info)

    except HTTPException:
        await db.rollback()
        raise

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Confliction happend")

    except Exception:
        logger.exception(
            f"Update person info by id failed with user id {current_user.user_id} for user {user_id}")

        await db.rollback()
        raise


async def unavctive_person_info(person_info: GetId, audit: AuditContext, current_user: Person, db: AsyncSession):
    if current_user.role != Roles.MANAGER:
        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=person_info.user_id,
            entity_type="person",
            event="PERSON_UNACTIVATED",
            old_value=None,
            new_value=None,
            status=AuditStatus.FAILED
        )
        await db.commit()

        raise HTTPException(
            status_code=403, detail=f"Not authorized to delete others' info.")

    try:
        result = await db.execute(select(Person).where(
            Person.user_id == person_info.user_id))

        searched_person = result.scalar_one_or_none()

        if searched_person is None:
            raise HTTPException(status_code=404, detail='Person not found')

        old_value = {column.key: getattr(searched_person, column.key)
                     for column in inspect(Person).mapper.column_attrs}

        searched_person.person_status = PersonStatus.UNACTIVE
        await db.flush()

        new_value = {column.key: getattr(searched_person, column.key)
                     for column in inspect(Person).mapper.column_attrs}

        new_value = make_json_format(new_value)
        old_value = make_json_format(old_value)

        await create_audit_log(
            db=db,
            audit=audit,
            user_id=current_user.user_id,
            entity_id=person_info.user_id,
            entity_type="person",
            event="PERSON_UNACTIVATED",
            old_value=old_value,
            new_value=new_value
        )
        await db.commit()

        return {"message": "Person deleted successfully."}

    except HTTPException:
        await db.rollback()
        raise

    except Exception:
        logger.exception("Unactinate the user wasn't successfulll")
        await db.rollback()
        raise
