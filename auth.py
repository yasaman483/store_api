from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, UTC, timedelta
import jwt
from pwdlib import PasswordHash
from config import setting
from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from models import People


password_hash = PasswordHash.recommended()
security = HTTPBearer(auto_error=False)


def hash_password(password: str):
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expire_delta: timedelta | None = None):
    to_encode = data.copy()
    if expire_delta:
        expire = datetime.now(UTC) + expire_delta
    else:
        expire = datetime.now(
            UTC) + timedelta(minutes=setting.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        setting.secret_key.get_secret_value(),
        algorithm=setting.algorithm)

    return encoded_jwt


def verify_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            setting.secret_key.get_secret_value(),
            algorithms=[setting.algorithm],
            options={"require": ["exp", "sub"]}
        )
    except jwt.InvalidTokenError:
        return None
    except Exception as e:
        print(e)
        return None
    else:
        return payload.get("sub")


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security), db: AsyncSession = Depends(get_db)):
    if credentials is None:
        return None

    token = credentials.credentials
    user_id = verify_access_token(token)

    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    try:
        user_id_int = int(user_id)
    except Exception as e:
        raise HTTPException(
            status_code=401, detail=f"Invalid or expired token based on error {e}")

    result = await db.execute(select(People).where(People.people_id == user_id_int))

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=404, detail=f"User {user_id} not found")

    return user
