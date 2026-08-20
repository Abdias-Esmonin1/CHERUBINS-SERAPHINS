"""Tests Phase 1 : cohérence des modèles SQLAlchemy existants avec le MCD validé.

Ne teste pas de connexion réelle à PostgreSQL (non disponible en CI
locale à ce stade) — vérifie uniquement la structure déclarée des
modèles via Base.metadata.
"""

from app.models import Base, Category, Language, Role, User


def test_expected_tables_are_registered() -> None:
    """Les tables Phase 1 (roles, categories, languages, users) et
    Phase 3 (artists, albums, songs) doivent exister.

    Mise à jour justifiée : cette assertion était initialement figée
    aux 4 tables de la Phase 1 ; elle est étendue ici pour refléter
    l'ajout légitime du catalogue (Phase 3), sans quoi ce test
    échouerait en permanence dès qu'une phase ajoute une table — ce
    qui n'est pas son objectif (vérifier qu'aucune table imprévue/hors
    MVP n'apparaît), documenté explicitement en Phase 3.

    Les tables encore hors périmètre (lyrics, translations, favorites,
    rights_records — Phases 4-7) ne doivent PAS encore être présentes.
    Les entités définitivement hors MVP (artist_aliases,
    lyrics_versions, sources, history) ne doivent JAMAIS apparaître.
    """
    table_names = set(Base.metadata.tables.keys())
    assert table_names == {"roles", "categories", "languages", "users", "artists", "albums", "songs"}


def test_role_check_constraint_restricts_to_user_and_admin() -> None:
    """Conforme à la décision validée : pas de rôle ARTIST en MVP."""
    roles_table = Role.__table__
    check_constraints = [c for c in roles_table.constraints if c.__class__.__name__ == "CheckConstraint"]
    assert any("USER" in str(c.sqltext) and "ADMIN" in str(c.sqltext) for c in check_constraints)


def test_user_has_soft_delete_column() -> None:
    """Conforme à la décision A (Livrable 1) : soft delete sur User."""
    assert "deleted_at" in User.__table__.columns


def test_user_password_hash_column_exists_and_is_not_plaintext_named() -> None:
    columns = User.__table__.columns
    assert "password_hash" in columns
    assert "password" not in columns


def test_category_and_language_have_unique_name_constraint() -> None:
    assert Category.__table__.columns["name"].unique
    assert Language.__table__.columns["name"].unique
