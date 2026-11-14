from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from models.people import Person
from database.connect import get_db
from crud.people import sign_up, login_for_access_token, get_all_people_info, update_info, unavctive_person_info, me
from schemas.people import PersonCreate, PersonResponse, FullPersonInfo, PersonUpdate, LoginRequest, LoginResponse, GetId, FilterPeople, GetPeopleInfo
import auth
from fastapi.security import HTTPAuthorizationCredentials
from crud.audit_log import create_audit_context


router = APIRouter(prefix="/people", tags=["People"])


@router.post("/sign_up", response_model=FullPersonInfo)
async def add(person: PersonCreate, request: Request, db: AsyncSession = Depends(get_db), current_user: Person | None = Depends(auth.get_user_sign_up)):
    audit = create_audit_context(request)
    return await sign_up(person, audit, db, current_user)


@router.post('/login', response_model=LoginResponse)
async def login(login_data: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await login_for_access_token(login_data, audit, db)


@router.post('/me', response_model=PersonResponse)
async def read_current_user_info(credentials: HTTPAuthorizationCredentials | None = Depends(auth.security), db: AsyncSession = Depends(get_db)):
    return await me(credentials, db)


@router.post('/get_all_people_info', response_model=GetPeopleInfo)
async def read_all_people_info(request: Request, filter_people_info: FilterPeople, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await get_all_people_info(audit, filter_people_info, current_user, db)


@router.patch('/edit_info', response_model=FullPersonInfo)
async def edit_person(person: PersonUpdate, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await update_info(person, audit, current_user, db)


@router.delete('/delete_person_info')
async def remove_person_info(person_info: GetId, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await unavctive_person_info(person_info, audit, current_user, db)
