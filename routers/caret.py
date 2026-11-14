from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from database.connect import get_db
from schemas.caret import GetCarets
from crud.people import Person
import auth
from crud.caret import get_caret_items
from schemas.caret import FilterCaret

router = APIRouter(prefix='/carets', tags=["Carets"])


@router.post('/get_carets', response_model=GetCarets)
async def read_carets(filter_caret: FilterCaret, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_caret_items(filter_caret, current_user, db)
