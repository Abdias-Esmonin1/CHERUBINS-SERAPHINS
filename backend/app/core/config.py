"""Configuration de l'application, chargée depuis les variables d'environnement.

Aucune valeur sensible n'est codée en dur ici : tout provient de .env
(non versionné) via pydantic-settings. Voir .env.example pour la liste
des variables attendues.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Environnement
    environment: str = "development"

    # Base de données
    database_url: str

    # Sécurité / JWT
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # CORS
    cors_origins: str = "http://localhost:3000"

    # Redis (réservé — non utilisé par le code applicatif en MVP,
    # cf. Livrable 2 §5, décision validée)
    redis_url: str | None = None

    # Logs
    log_level: str = "INFO"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Retourne une instance unique (mise en cache) des settings."""
    return Settings()
