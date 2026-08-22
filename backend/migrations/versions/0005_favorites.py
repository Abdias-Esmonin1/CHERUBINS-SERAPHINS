"""favorites — chansons favorites des utilisateurs

Revision ID: 0005
Revises: 0004
Create Date: 2026-08-22

Ajoute la table `favorites` (Phase 6). Aucune notion de droits/statut
ici — ressource strictement privée à son propriétaire. `ON DELETE
CASCADE` sur les deux FK (contrairement à `RESTRICT` utilisé pour
lyrics/translations, où la traçabilité prime).

Écrite manuellement (pas d'autogenerate), même limitation que les
migrations précédentes : aucun serveur PostgreSQL disponible dans
l'environnement d'implémentation. Contenu vérifié ligne à ligne contre
le modèle SQLAlchemy réel (favorite.py).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "favorites",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "song_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("songs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "song_id", name="uq_favorites_user_song"),
    )
    op.create_index("idx_favorites_user_id", "favorites", ["user_id"])
    op.create_index("idx_favorites_song_id", "favorites", ["song_id"])


def downgrade() -> None:
    op.drop_index("idx_favorites_song_id", table_name="favorites")
    op.drop_index("idx_favorites_user_id", table_name="favorites")
    op.drop_table("favorites")
