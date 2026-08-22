"""Point d'entrée de l'application FastAPI — CHERUBINS SERAPHINS.

Phase 1 (Backend Foundation) : uniquement l'infrastructure (config,
CORS, gestion d'erreurs, healthcheck). Les routers métier
(/api/v1/auth, songs, lyrics, ...) sont ajoutés dans les phases
suivantes, conformément à l'ordre d'implémentation validé.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.exceptions.handlers import register_exception_handlers
from app.routers import albums, artists, auth, categories, languages, lyrics, songs

settings = get_settings()

logging.basicConfig(level=settings.log_level)

app = FastAPI(
    title="CHERUBINS SERAPHINS API",
    version="0.1.0",
    description="API de recherche et consultation de paroles de chants chrétiens.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Healthcheck hors versionnement /api/v1 (Livrable 3 §12)."""
    return {"status": "ok", "environment": settings.environment}


app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(categories.router, prefix="/api/v1/categories", tags=["categories"])
app.include_router(languages.router, prefix="/api/v1/languages", tags=["languages"])
app.include_router(artists.router, prefix="/api/v1/artists", tags=["artists"])
app.include_router(albums.router, prefix="/api/v1/albums", tags=["albums"])
app.include_router(songs.router, prefix="/api/v1/songs", tags=["songs"])
app.include_router(lyrics.router, prefix="/api/v1/lyrics", tags=["lyrics"])

# Les routers métier des phases suivantes seront inclus ici :
# app.include_router(translations.router, prefix="/api/v1/translations", tags=["translations"])
