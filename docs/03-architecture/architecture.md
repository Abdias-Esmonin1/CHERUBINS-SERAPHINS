# Architecture technique — CHERUBINS SERAPHINS

**Version :** 1.0 (MVP) — Livrable 2, consolidé
**Statut :** Référence validée

---

## 1. Architecture globale

```
Utilisateur (mobile/desktop)
        |
     Next.js / React (frontend)
        |
     FastAPI (backend, /api/v1)
        |
     PostgreSQL 16
        |
     Redis (déclaré, non utilisé par le code applicatif en MVP)
        |
     pgvector (extension future, non activée en MVP)
```

Aucune communication directe frontend <-> PostgreSQL. Toute donnée
transite par l'API. Les services externes (Spotify, YouTube) restent
hors MVP et ne seront jamais une source automatique de paroles
(Stratégie de contenu §8, §13).

## 2. Architecture backend (FastAPI)

Pattern : **Router -> Service -> Repository -> Model**. Un router
n'appelle jamais SQLAlchemy directement ; un service ne construit
jamais de réponse HTTP.

```
backend/app/
├── main.py
├── core/          # config, database, security, dependencies
├── models/        # SQLAlchemy 2.x
├── schemas/        # Pydantic v2 (à partir de la Phase 2)
├── repositories/    # accès données pur (à partir de la Phase 2)
├── services/         # logique métier (à partir de la Phase 2)
├── routers/           # endpoints HTTP (à partir de la Phase 2)
├── exceptions/          # exceptions métier + handler global
└── tests/
```

**État Phase 1** : `core/`, `exceptions/`, `main.py` (avec `/health`),
Alembic configurés.

**État Phase 2** : authentification complète implémentée en suivant
strictement le pattern Router -> Service -> Repository -> Model :
- `schemas/auth.py`, `schemas/user.py` (Pydantic v2)
- `repositories/user_repository.py`, `repositories/role_repository.py`
- `services/auth_service.py` (register, login, résolution utilisateur
  depuis JWT)
- `routers/auth.py` (`/api/v1/auth/{register,login,logout,me}`)
- `core/dependencies.py` complété : `get_current_user`, `require_admin`
- `core/security.py` complété : nom du cookie JWT (`ACCESS_TOKEN_COOKIE_NAME`)

Le JWT est posé exclusivement via cookie `HttpOnly` — jamais dans le
corps JSON (décision explicite Phase 2, qui précise le Livrable 3
§2.1 initial). Voir `docs/05-api/api.md` pour le détail.

**État Phase 3** : catalogue Artists → Albums → Songs implémenté
(`models/{artist,album,song}.py`, `schemas/`, `repositories/`,
`services/catalog_service.py`, `routers/{artists,albums,songs,
categories,languages}.py`). Recherche par `ILIKE` (limitation
documentée, voir `docs/05-api/api.md`). CRUD `PUT`/`DELETE` sur
artists/albums/categories/languages différé (non implémenté en Phase
3, périmètre volontairement centré sur Artists → Albums → Songs).

## 3. Architecture frontend (Next.js)

Non démarrée (Phase 8). Voir Livrable 5 pour la spécification
complète (routes, composants, design system, tokens).

## 4. Architecture PostgreSQL

Modèle de données MVP (Livrable 1, validé) :
```
users, roles, categories, languages, artists, albums, songs,
lyrics, translations, favorites, rights_records
```
Hors MVP (décision définitive) : `artist_aliases`, `lyrics_versions`,
`sources` (remplacée par des champs `source_type`/`source_url` sur
`lyrics`/`translations`), `history`.

Détail complet des colonnes/contraintes : `docs/04-database/database.md`.

**État Phase 1** : 4 tables créées (`roles`, `categories`, `languages`,
`users`), migration `0001_initial`. Les 7 tables restantes seront
ajoutées phase par phase (Catalogue, Lyrics, Translations, Favorites,
Admin).

## 5. Architecture Redis

Non utilisé par le code applicatif en MVP. Déclaré dans
`docker-compose.yml` par anticipation (Livrable 2 §5, décision
validée).

## 6. Sécurité

- Mots de passe : bcrypt (`core/security.py`, Phase 1 — utilitaires
  prêts, pas encore branchés à des endpoints).
- JWT : HS256, access token courte durée, sans refresh token (décision
  validée, Livrable 2 §13).
- Permissions : `roles.name IN ('USER','ADMIN')` uniquement, pas de
  RBAC fin en MVP.
- Aucune exception brute (SQLAlchemy, Python) ne fuite vers le client
  (`exceptions/handlers.py`, Phase 1).

## 7. Règle fondamentale des droits (rappel)

```
authorization_status == AUTHORIZED
AND (expiration_date IS NULL OR expiration_date >= now())
  -> contenu visible publiquement

Auteur (submitted_by_user_id == current_user.id)
  -> contenu toujours visible, quel que soit le statut

ADMIN
  -> contenu toujours visible
```
Appliquée exclusivement côté backend (service), jamais côté frontend
seul. `rights_records` est append-only (aucun `PUT`/`PATCH`/`DELETE`).

**État Phase 4** : système Lyrics implémenté (`models/lyrics.py`,
`schemas/lyrics.py`, `repositories/lyrics_repository.py`,
`services/lyrics_service.py`, `routers/lyrics.py`). Portée
strictement limitée à la soumission, la consultation avec visibilité
différenciée (public/auteur/ADMIN), et l'édition en `PENDING`
(**Option A validée**). `rights_records` et la modération admin
(`authorize`/`reject`/`revoke`) restent explicitement réservés à la
**Phase 7**. Nouvelle dépendance `get_current_user_optional`
(`core/dependencies.py`) — résout l'utilisateur courant sans lever 401,
nécessaire pour un endpoint public dont la réponse varie selon le
viewer.

## 8. Historique des décisions

Voir Livrables 1 à 5 (conception complète, validée avant
implémentation) pour le détail exhaustif des arbitrages, incohérences
résolues, et diagrammes de flux.
