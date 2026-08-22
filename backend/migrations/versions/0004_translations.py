"""translations — traductions des paroles

Revision ID: 0004
Revises: 0003
Create Date: 2026-08-22

Ajoute la table `translations` (Phase 5). Ne crée PAS `rights_records`
ni d'endpoints de modération (explicitement Phase 7, cf.
docs/roadmap.md et validation Option A, symétrique à la Phase 4).

Écrite manuellement (pas d'autogenerate), même limitation que les
migrations précédentes : aucun serveur PostgreSQL disponible dans
l'environnement d'implémentation. Contenu vérifié ligne à ligne contre
le modèle SQLAlchemy réel (translation.py).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "translations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "lyrics_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lyrics.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "target_language_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("languages.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("translation_type", sa.String(length=20), nullable=False),
        sa.Column("authorization_status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("expiration_date", sa.Date(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("rights_holder", sa.String(length=255), nullable=True),
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
        sa.UniqueConstraint("lyrics_id", "target_language_id", name="uq_translations_lyrics_language"),
        sa.CheckConstraint(
            "translation_type IN ('OFFICIAL', 'AUTHOR', 'HUMAN', 'AI_GENERATED')",
            name="ck_translations_type",
        ),
        sa.CheckConstraint(
            "authorization_status IN ('PENDING', 'AUTHORIZED', 'REJECTED', 'EXPIRED', 'REVOKED')",
            name="ck_translations_authorization_status",
        ),
    )
    op.create_index("idx_translations_lyrics_id", "translations", ["lyrics_id"])
    op.create_index("idx_translations_target_language_id", "translations", ["target_language_id"])
    op.create_index("idx_translations_authorization_status", "translations", ["authorization_status"])
    op.create_index("idx_translations_submitted_by_user_id", "translations", ["submitted_by_user_id"])


def downgrade() -> None:
    op.drop_index("idx_translations_submitted_by_user_id", table_name="translations")
    op.drop_index("idx_translations_authorization_status", table_name="translations")
    op.drop_index("idx_translations_target_language_id", table_name="translations")
    op.drop_index("idx_translations_lyrics_id", table_name="translations")
    op.drop_table("translations")
