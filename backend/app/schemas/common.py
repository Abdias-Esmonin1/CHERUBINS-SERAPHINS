"""Schémas partagés — pagination (convention Livrable 3 §13)."""

from pydantic import BaseModel


class PaginationMeta(BaseModel):
    page: int
    page_size: int
    total: int
    total_pages: int
