from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.repositories.language_repository import LanguageRepository
from app.schemas.language import LanguageRead

router = APIRouter()


@router.get("")
async def list_languages(only_active: bool = False, db: AsyncSession = Depends(get_db)) -> dict:
    languages = await LanguageRepository(db).list_all(only_active=only_active)
    return {"data": [LanguageRead.model_validate(l) for l in languages]}
