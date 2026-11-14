from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from models.people import Person
from database.connect import get_db
from crud.caret_items import create_caret_items, get_caret_items, update_caret_items, update_caret_items_status, delete_caret_items
from schemas.caret_items import CaretItemsResponse, GetCaretItems, FilterCaretItems, RemoveCaretItems, CaretItemUpdateStatus, InfoCaretItems
from crud.audit_log import create_audit_context
import auth
from schemas.orders import FullOrderResponse


router = APIRouter(prefix='/caret_items', tags=["CaretItems"])


@router.post('/create_caret_items', response_model=list[CaretItemsResponse])
async def add_caret_items(request: Request, items: InfoCaretItems, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await create_caret_items(audit, items, current_user, db)


@router.post('/get_caret_items', response_model=GetCaretItems)
async def read_caret_items(caret: FilterCaretItems, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    return await get_caret_items(caret, current_user, db)


@router.patch('/update_caret_items', response_model=list[CaretItemsResponse])
async def edit_caret_items(items: InfoCaretItems, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await update_caret_items(items, audit, current_user, db)


@router.patch('/update_caret_items_status', response_model=FullOrderResponse)
async def edit_caret_items_status(items: CaretItemUpdateStatus, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await update_caret_items_status(items, audit, current_user, db)


@router.delete('/delete_caret_items', response_model=list[CaretItemsResponse] | dict)
async def remove_caret_items(items: RemoveCaretItems, request: Request, current_user: Person = Depends(auth.get_current_user), db: AsyncSession = Depends(get_db)):
    audit = create_audit_context(request)
    return await delete_caret_items(items, audit, current_user, db)
