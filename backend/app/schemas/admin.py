"""Schémas Pydantic pour les statistiques admin."""

from pydantic import BaseModel


class LyricsStatusCounts(BaseModel):
    PENDING: int = 0
    AUTHORIZED: int = 0
    REJECTED: int = 0
    EXPIRED: int = 0
    REVOKED: int = 0


class AdminStatsRead(BaseModel):
    users_count: int
    songs_count: int
    artists_count: int
    albums_count: int
    categories_count: int
    languages_count: int
    favorites_count: int
    lyrics_by_status_count: LyricsStatusCounts
