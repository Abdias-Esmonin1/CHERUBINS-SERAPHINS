"""rights_records + translations moderation columns

Revision ID: 0006
Revises: 0005
Create Date: 2026-08-23

Phase 7 — Administration / Modération / Traçabilité.

Choix technique documenté (consigne §17) : cette migration regroupe
DEUX changements dans un seul fichier plutôt que de les séparer :
1. Création de la table `rights_records` (journal d'audit append-only).
2. Ajout de `authorization_reference` et `authorization_date` sur
   `translations` (Option A validée — ces colonnes existaient déjà sur
   `lyrics` depuis la Phase 1/4 ; leur absence sur `translations`
   était une exclusion volontaire de la Phase 5, devenue nécessaire
   maintenant que l'endpoint `PATCH /admin/translations/{id}/authorize`
   doit pouvoir les enregistrer).
Justification du regroupement : les deux changements appartiennent au
même changement fonctionnel cohérent (Phase 7 — rendre le workflow de
modération complet et symétrique entre lyrics et translations) ; les
séparer en deux migrations n'apporterait aucun bénéfice de
réversibilité indépendante réelle, puisque l'une ne fait sens sans
l'autre pour cette phase. Une seule migration atomique est donc plus
simple à raisonner et à appliquer.

Écrite manuellement (pas d'autogenerate), même limitation que les
migrations précédentes : aucun serveur PostgreSQL disponible dans
l'environnement d'implémentation. Contenu vérifié ligne à ligne contre
les modèles SQLAlchemy réels (rights_record.py, translation.py).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    # --- 1. Colonnes de modération sur translations (Option A) ---
    op.add_column("translations", sa.Column("authorization_reference", sa.String(length=100), nullable=True))
    op.add_column("translations", sa.Column("authorization_date", sa.Date(), nullable=True))

    # --- 2. Table rights_records ---
    op.create_table(
        "rights_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "lyrics_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("lyrics.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column(
            "translation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("translations.id", ondelete="RESTRICT"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=20), nullable=False),
        sa.Column("previous_status", sa.String(length=20), nullable=True),
        sa.Column("new_status", sa.String(length=20), nullable=False),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column(
            "performed_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint(
            "(lyrics_id IS NOT NULL AND translation_id IS NULL) OR "
            "(lyrics_id IS NULL AND translation_id IS NOT NULL)",
            name="ck_rights_records_exactly_one_target",
        ),
        sa.CheckConstraint(
            "action IN ('VALIDATED', 'REJECTED', 'REVOKED')",
            name="ck_rights_records_action",
        ),
    )
    op.create_index("idx_rights_records_lyrics_id", "rights_records", ["lyrics_id"])
    op.create_index("idx_rights_records_translation_id", "rights_records", ["translation_id"])
    op.create_index("idx_rights_records_action", "rights_records", ["action"])
    op.create_index("idx_rights_records_performed_by_user_id", "rights_records", ["performed_by_user_id"])


def downgrade() -> None:
    op.drop_index("idx_rights_records_performed_by_user_id", table_name="rights_records")
    op.drop_index("idx_rights_records_action", table_name="rights_records")
    op.drop_index("idx_rights_records_translation_id", table_name="rights_records")
    op.drop_index("idx_rights_records_lyrics_id", table_name="rights_records")
    op.drop_table("rights_records")

    op.drop_column("translations", "authorization_date")
    op.drop_column("translations", "authorization_reference")
