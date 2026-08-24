"""Service Admin — statistiques agrégées.

Requêtes de comptage directes (pas de repository dédié : usage
suffisamment simple et localisé pour ne pas justifier une couche
supplémentaire, cohérent avec le principe de simplicité déjà appliqué
ailleurs dans le projet)."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.album import Album
from app.models.artist import Artist
from app.models.category import Category
from app.models.favorite import Favorite
from app.models.language import Language
from app.models.lyrics import Lyrics
from app.models.song import Song
from app.models.user import User
from app.schemas.admin import AdminStatsRead, LyricsStatusCounts


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_stats(self) -> AdminStatsRead:
        async def count(model) -> int:
            result = await self._session.execute(select(func.count()).select_from(model))
            return result.scalar_one()

        status_result = await self._session.execute(
            select(Lyrics.authorization_status, func.count()).group_by(Lyrics.authorization_status)
        )
        status_counts = LyricsStatusCounts()
        for status, cnt in status_result.all():
            if hasattr(status_counts, status):
                setattr(status_counts, status, cnt)

        return AdminStatsRead(
            users_count=await count(User),
            songs_count=await count(Song),
            artists_count=await count(Artist),
            albums_count=await count(Album),
            categories_count=await count(Category),
            languages_count=await count(Language),
            favorites_count=await count(Favorite),
            lyrics_by_status_count=status_counts,
        )
