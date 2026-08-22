"""lyrics — paroles originales

Revision ID: 0003
Revises: 0002
Create Date: 2026-08-21

Ajoute la table `lyrics` (Phase 4). Ne crée PAS `rights_records`
(explicitement Phase 7, cf. docs/roadmap.md et validation Option A).

Écrite manuellement (pas d'autogenerate), même limitation que 0001/0002 :
aucun serveur PostgreSQL disponible dans l'environnement
d'implémentation. Contenu vérifié ligne à ligne contre le modèle
SQLAlchemy réel (lyrics.py).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lyrics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "song_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("songs.id", ondelete="RESTRICT"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "language_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("languages.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=20), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("rights_holder", sa.String(length=255), nullable=True),
        sa.Column("authorization_status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("authorization_reference", sa.String(length=100), nullable=True),
        sa.Column("authorization_date", sa.Date(), nullable=True),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column(
            "submitted_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "reviewed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.CheckConstraint(
            "source_type IN ('ORIGINAL', 'ARTIST', 'RIGHTS_HOLDER', 'LICENSE', 'PARTNER', "
            "'PUBLIC_DOMAIN', 'USER_SUBMITTED')",
            name="ck_lyrics_source_type",
        ),
        sa.CheckConstraint(
            "authorization_status IN ('PENDING', 'AUTHORIZED', 'REJECTED', 'EXPIRED', 'REVOKED')",
            name="ck_lyrics_authorization_status",
        ),
    )
    op.create_index("idx_lyrics_authorization_status", "lyrics", ["authorization_status"])
    op.create_index("idx_lyrics_source_type", "lyrics", ["source_type"])
    op.create_index("idx_lyrics_submitted_by_user_id", "lyrics", ["submitted_by_user_id"])


def downgrade() -> None:
    op.drop_index("idx_lyrics_submitted_by_user_id", table_name="lyrics")
    op.drop_index("idx_lyrics_source_type", table_name="lyrics")
    op.drop_index("idx_lyrics_authorization_status", table_name="lyrics")
    op.drop_table("lyrics")
