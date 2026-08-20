"""Handlers d'exceptions globaux, enregistrés dans main.py.

Garantit l'enveloppe d'erreur standard (Livrable 3 §21) :
    {"error": {"code": ..., "message": ..., "details": ...}}
et empêche toute exception brute (SQLAlchemy, Python) de fuiter vers
le client.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.errors import AppError

logger = logging.getLogger("cherubins_seraphins")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": exc.code, "message": exc.message, "details": exc.details}},
        )

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        # Aucune trace technique n'est jamais exposée au client (CLAUDE.md §8).
        logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Une erreur interne est survenue.",
                    "details": None,
                }
            },
        )
