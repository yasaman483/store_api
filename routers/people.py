from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models.people import People
from database.connect import get_db
from crud.people import sign_up, login_for_access_token, get_all_people_info, update_info, delete_person_info, get_people_by_id, get_current_user
from schemas.people import PeopleCreate, PeopleResponse, PeopleUpdate, LoginRequest, LoginResponse, GetId
import auth
from fastapi.security import HTTPAuthorizationCredentials


router = APIRouter(prefix="/people", tags=["People"])


@router.post("/sign_up", response_model=PeopleResponse)
async def add(person: PeopleCreate, db: AsyncSession = Depends(get_db), current_user: People | None = Depends(auth.get_current_user)):
    return await sign_up(person, db, current_user)


@router.post('/login', response_model=LoginResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await login_for_access_token(login_data, db)


@router.post('/me', response_model=PeopleResponse)
async def read_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(auth.security), db: AsyncSession = Depends(get_db)):
    return await get_current_user(credentials, db)


@router.post('/get_all_people_info', response_model=list[PeopleResponse])
async def read_all_people_info(current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_all_people_info(current_user, db)


@router.post('/get_people_info_by_id', response_model=PeopleResponse)
async def read_people_by_id(person: GetId, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_people_by_id(person, current_user, db)


@router.put('/edit_info', response_model=PeopleResponse)
async def edit_person(person: PeopleUpdate, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_info(person, current_user, db)


@router.delete('/delete')
async def remove_person_info(person_info: GetId, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await delete_person_info(person_info, current_user, db)


# @router.post("/sign_up", response_model=PeopleResponse)
# async def add_customer(person: CustomerCreate, db: AsyncSession = Depends(get_db)):
#     return await sign_up(person, db)


# @router.post("/add_employee", response_model=PeopleResponse)
# async def add_employees(person: EmployeeCreate, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
#     return await add_employee(person, current_user, db)

# @router.put('/edit', response_model=PeopleResponse)
# async def edit_person(person: CustomerUpdate, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
#     return await update_person_info(person, current_user, db)


# @router.put('/edit_employee', response_model=PeopleResponse)
# async def edit_employee(current_info: EmployeeUpdateGet, new_info: EmployeeUpdateSent, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
#     return await update_employee_info(current_info, new_info, current_user, db)

# @router.post('/get_people_by_phone', response_model=PeopleResponse)
# async def read_people_by_phone(person: GetPhone, current_user: People = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
#     return await get_people_by_phone(person, current_user, db)
