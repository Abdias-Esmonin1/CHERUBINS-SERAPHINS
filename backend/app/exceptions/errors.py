"""Exceptions métier custom.

Un service lève ces exceptions ; jamais une HTTPException directement
(cf. Livrable 2 §2.4, règle de dépendance Router -> Service ->
Repository -> Model). Le handler global (exceptions/handlers.py) les
traduit en réponse HTTP standardisée.
"""


class AppError(Exception):
    """Exception métier de base."""

    code: str = "APP_ERROR"
    status_code: int = 500

    def __init__(self, message: str, details: dict | None = None) -> None:
        self.message = message
        self.details = details
        super().__init__(message)


class NotFoundError(AppError):
    code = "NOT_FOUND"
    status_code = 404


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"
    status_code = 401


class ForbiddenError(AppError):
    code = "FORBIDDEN"
    status_code = 403


class ConflictError(AppError):
    code = "CONFLICT"
    status_code = 409
