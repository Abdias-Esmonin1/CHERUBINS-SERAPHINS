from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.category_repository import CategoryRepository
from app.schemas.category import CategoryRead

router = APIRouter()


@router.get("")
async def list_categories(db: AsyncSession = Depends(get_db)) -> dict:
    categories = await CategoryRepository(db).list_all()
    return {"data": [CategoryRead.model_validate(c) for c in categories]}
