from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_admin
from app.models.user import User
from app.services.admin_service import AdminService

router = APIRouter()


@router.get("")
async def get_stats(db: AsyncSession = Depends(get_db), _admin: User = Depends(require_admin)) -> dict:
    service = AdminService(db)
    stats = await service.get_stats()
    return {"data": stats}
