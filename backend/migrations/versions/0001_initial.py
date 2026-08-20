"""initial schema — roles, categories, languages, users

Revision ID: 0001
Revises:
Create Date: 2026-08-20

Reflète exactement les modèles SQLAlchemy présents dans
backend/app/models/ à ce stade (Phase 1 — Backend Foundation) :
Role, Category, Language, User.

Les tables métier restantes (artists, albums, songs, lyrics,
translations, favorites, rights_records) appartiennent aux phases
suivantes et ne sont pas créées ici, conformément à la stratégie
d'implémentation progressive.

Écrite manuellement (pas d'autogenerate) : aucun serveur PostgreSQL
n'était disponible dans l'environnement d'implémentation pour générer
cette migration automatiquement. Le contenu a été vérifié ligne à
ligne contre les définitions de modèles existantes.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=50), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("name IN ('USER', 'ADMIN')", name="ck_roles_name"),
    )
    op.create_index("idx_roles_name", "roles", ["name"])

    op.create_table(
        "categories",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "languages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(length=10), nullable=False, unique=True),
        sa.Column("name", sa.String(length=100), nullable=False, unique=True),
        sa.Column("native_name", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("role_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("roles.id"), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False, unique=True),
        sa.Column("first_name", sa.String(length=150), nullable=True),
        sa.Column("last_name", sa.String(length=150), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("email LIKE '%@%'", name="ck_users_email_format"),
        sa.CheckConstraint("CHAR_LENGTH(username) >= 3", name="ck_users_username_length"),
    )
    op.create_index("idx_users_role_id", "users", ["role_id"])
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_username", "users", ["username"])


def downgrade() -> None:
    op.drop_index("idx_users_username", table_name="users")
    op.drop_index("idx_users_email", table_name="users")
    op.drop_index("idx_users_role_id", table_name="users")
    op.drop_table("users")

    op.drop_table("languages")
    op.drop_table("categories")

    op.drop_index("idx_roles_name", table_name="roles")
    op.drop_table("roles")
