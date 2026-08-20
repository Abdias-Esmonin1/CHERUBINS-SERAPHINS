"""Dépendances FastAPI partagées.

Note : get_current_user et require_admin (authentification/autorisation)
sont volontairement absentes de cette Phase 1 — elles seront ajoutées en
Phase 2 avec le reste du flux d'authentification (register/login/me),
conformément à l'ordre d'implémentation validé. Introduire ces
dépendances maintenant nécessiterait de coder la logique JWT->User
avant que les endpoints d'auth n'existent, ce qui déborderait sur la
Phase 2.
"""

from dataclasses import dataclass


@dataclass
class Pagination:
    page: int = 1
    page_size: int = 20


def get_pagination(page: int = 1, page_size: int = 20) -> Pagination:
    """Normalise les paramètres de pagination (convention Livrable 3 §13)."""
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    return Pagination(page=page, page_size=page_size)
