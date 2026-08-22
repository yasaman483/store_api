from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models.people import Person
from database.connect import get_db
from crud.people import sign_up, login_for_access_token, get_all_people_info, update_info, delete_person_info, get_person_by_id, get_current_user
from schemas.people import PersonCreate, PersonResponse, PersonUpdate, LoginRequest, LoginResponse, GetId
import auth
from fastapi.security import HTTPAuthorizationCredentials


router = APIRouter(prefix="/people", tags=["People"])


@router.post("/sign_up", response_model=PersonResponse)
async def add(person: PersonCreate, db: AsyncSession = Depends(get_db), current_user: Person | None = Depends(auth.get_current_user)):
    return await sign_up(person, db, current_user)


@router.post('/login', response_model=LoginResponse)
async def login(login_data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await login_for_access_token(login_data, db)


@router.post('/me', response_model=PersonResponse)
async def read_current_user_info(credentials: HTTPAuthorizationCredentials = Depends(auth.security), db: AsyncSession = Depends(get_db)):
    return await get_current_user(credentials, db)


@router.post('/get_all_people_info', response_model=list[PersonResponse])
async def read_all_people_info(current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_all_people_info(current_user, db)


@router.post('/get_person_info_by_id', response_model=PersonResponse)
async def read_person_by_id(person: GetId, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_person_by_id(person, current_user, db)


@router.put('/edit_info', response_model=PersonResponse)
async def edit_person(person: PersonUpdate, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await update_info(person, current_user, db)


@router.delete('/delete_person_info')
async def remove_person_info(person_info: GetId, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await delete_person_info(person_info, current_user, db)
