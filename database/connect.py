from dotenv import load_dotenv
import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import logging

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


load_dotenv('./database/.env')
engine = create_async_engine(
    f"mysql+aiomysql://root:{os.getenv('db_pass')}@localhost:3306/store2")

AsyncSessionLocal = async_sessionmaker(
    autoflush=False, autocommit=False, bind=engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as AsyncSession:
        yield AsyncSession
