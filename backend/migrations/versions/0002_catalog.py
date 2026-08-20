"""catalog — artists, albums, songs

Revision ID: 0002
Revises: 0001
Create Date: 2026-08-20

Ajoute les 3 tables du catalogue (Phase 3), plus les relations
inverses vers `categories`/`languages` déjà existantes (aucune
modification de structure sur ces deux tables, seules des FK entrantes
sont ajoutées via `songs`).

Écrite manuellement (pas d'autogenerate), même limitation que
0001_initial : aucun serveur PostgreSQL disponible dans l'environnement
d'implémentation. Contenu vérifié ligne à ligne contre les modèles
SQLAlchemy réels (artist.py, album.py, song.py).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "artists",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("slug", sa.String(length=220), nullable=False, unique=True),
        sa.Column("biography", sa.Text(), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("image_url", sa.Text(), nullable=True),
        sa.Column("official_links", postgresql.JSONB(), nullable=True),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_artists_slug", "artists", ["slug"])

    op.create_table(
        "albums",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "artist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artists.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("release_year", sa.SmallInteger(), nullable=True),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    op.create_index("idx_albums_artist_id", "albums", ["artist_id"])

    op.create_table(
        "songs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=280), nullable=False, unique=True),
        sa.Column(
            "artist_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("artists.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "album_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("albums.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "category_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("categories.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "original_language_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("languages.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("cover_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("external_provider", sa.String(length=50), nullable=True),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("external_url", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')", name="ck_songs_status"),
    )
    op.create_index("idx_songs_artist_id", "songs", ["artist_id"])
    op.create_index("idx_songs_album_id", "songs", ["album_id"])
    op.create_index("idx_songs_category_id", "songs", ["category_id"])
    op.create_index("idx_songs_original_language_id", "songs", ["original_language_id"])
    op.create_index("idx_songs_status", "songs", ["status"])


def downgrade() -> None:
    op.drop_index("idx_songs_status", table_name="songs")
    op.drop_index("idx_songs_original_language_id", table_name="songs")
    op.drop_index("idx_songs_category_id", table_name="songs")
    op.drop_index("idx_songs_album_id", table_name="songs")
    op.drop_index("idx_songs_artist_id", table_name="songs")
    op.drop_table("songs")

    op.drop_index("idx_albums_artist_id", table_name="albums")
    op.drop_table("albums")

    op.drop_index("idx_artists_slug", table_name="artists")
    op.drop_table("artists")
