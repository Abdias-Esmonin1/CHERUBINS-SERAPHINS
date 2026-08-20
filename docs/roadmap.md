# Roadmap — CHERUBINS SERAPHINS

## Ordre d'implémentation validé

| Phase | Contenu | Statut |
|---|---|---|
| 1 | Backend Foundation (config, DB, Alembic, /health, tests) | ✅ Terminée |
| 2 | Authentication (register/login/logout/me) | ⏳ À venir |
| 3 | Catalogue (songs/artists/albums/categories/languages) | ⏳ À venir |
| 4 | Lyrics | ⏳ À venir |
| 5 | Translations | ⏳ À venir |
| 6 | Favorites | ⏳ À venir |
| 7 | Administration (modération, rights records) | ⏳ À venir |
| 8 | Frontend Next.js | ⏳ À venir |
| 9 | Tests (couverture complète) | ⏳ À venir |
| 10 | Docker / CI / finalisation | ⏳ À venir |

## Après le MVP (V2+, hors périmètre actuel)

- `history` (historique de consultation).
- Rôle `ARTIST` dédié.
- RBAC fin (`permissions`/`role_permissions`).
- Recherche sémantique (pgvector), fuzzy search.
- Redis effectif (cache, rate limiting).
- Intégration Spotify/YouTube (identification uniquement).
- Application mobile, recherche vocale/audio.

Détail complet : Cahier des charges §32-§33, Schéma directeur §43.
