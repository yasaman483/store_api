from database.connect import AsyncSessionLocal
from models.people import People
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import date
from auth import hash_password
from schemas.people import Roles


async def seed_manager():
    db: AsyncSession = AsyncSessionLocal()
    result = await db.execute(select(People))
    people = result.scalars().all()

    if not people:
        manager = People(
            first_name='manager',
            last_name='manager',
            password_hash=hash_password('111111111'),
            birth_date=date.today(),
            phone='09000000000',
            address='managerAddress',
            city='managerCity',
            role=Roles.MANAGER
        )

        try:
            db.add(manager)
            await db.commit()

        except Exception as e:
            await db.rollback()
            raise e

    await db.close()
