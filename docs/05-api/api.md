# API — CHERUBINS SERAPHINS

**Référence complète (spécification) :** Livrable 3, validé.
Ce document ne décrit que ce qui est **réellement implémenté**.

## Convention générale

- Préfixe `/api/v1` pour toutes les routes métier. `/health` hors
  préfixe.
- JSON exclusivement. Enveloppe standard :
  - Succès : `{"data": {...}}`
  - Erreur : `{"error": {"code": ..., "message": ..., "details": ...}}`

## Implémenté — Phase 1

```
GET /health
```
Healthcheck, hors authentification.

## Implémenté — Phase 2 (Authentication)

```
POST /api/v1/auth/register
POST /api/v1/auth/login
POST /api/v1/auth/logout
GET  /api/v1/auth/me
```

### Écart documenté avec le Livrable 3 initial

Le Livrable 3 (§2.1) montrait initialement `access_token` dans le
corps JSON de `register`/`login`. Les instructions de la Phase 2 ont
explicitement tranché : **le JWT n'est jamais retourné en JSON**,
uniquement posé via un cookie `HttpOnly` (`access_token`,
`SameSite=Lax`, `Secure` en production, `max_age` = durée du token).
`register` et `login` retournent uniquement les données utilisateur
publiques (`UserPublicRead`).

### Détail des endpoints

**POST /auth/register**
- Auth : non.
- Body : `{email, username, password}` (`role`, `password_hash`,
  `is_verified`, `deleted_at` absents du schéma — ne peuvent pas être
  fournis par le client).
- 201 : `{"data": UserPublicRead}` + cookie posé.
- Erreurs : `409 EMAIL_ALREADY_EXISTS`, `409 USERNAME_ALREADY_EXISTS`,
  `422` (validation Pydantic : email invalide, mot de passe < 8
  caractères, username < 3 caractères ou avec espaces).
- Règle : rôle forcé à `USER`, mot de passe hashé (bcrypt) avant
  stockage.

**POST /auth/login**
- Auth : non.
- Body : `{email, password}`.
- 200 : `{"data": UserPublicRead}` + cookie posé.
- Erreurs : `401 INVALID_CREDENTIALS` (message identique que l'email
  existe ou non — anti-énumération), `403 ACCOUNT_DISABLED` si
  `is_active = false`.
- Effet : met à jour `last_login_at`.

**POST /auth/logout**
- Auth : non requise (idempotent, y compris sans session active).
- 204, supprime le cookie `access_token`.

**GET /auth/me**
- Auth : oui (cookie `access_token`).
- 200 : `{"data": UserPublicRead}` — `{id, email, username, role,
  is_verified, created_at}`. Jamais `password_hash`.
- Erreurs : `401 UNAUTHORIZED` (cookie absent, token invalide/expiré,
  utilisateur introuvable/désactivé/soft-deleted).

## Implémenté — Phase 3 (Catalogue)

```
GET  /api/v1/categories
GET  /api/v1/languages
GET  /api/v1/artists
GET  /api/v1/artists/{slug}
POST /api/v1/artists                [ADMIN]
GET  /api/v1/albums
GET  /api/v1/albums/{album_id}
POST /api/v1/albums                 [ADMIN]
GET  /api/v1/songs
GET  /api/v1/songs/search
GET  /api/v1/songs/{slug}
POST /api/v1/songs                  [ADMIN]
PUT  /api/v1/songs/{song_id}        [ADMIN]
```

### Détail

**GET /categories**, **GET /languages** : lecture publique, pas de
pagination (volume faible attendu, conforme Livrable 3 §6-7).

**GET /artists** : pagination + filtres `country`, `is_verified`.
**GET /artists/{slug}** : 404 `ARTIST_NOT_FOUND` si absent/soft-deleted.
**POST /artists** [ADMIN] : body `{name, biography?, country?,
image_url?, official_links?}` — **`slug` jamais fourni par le client,
généré côté serveur** (conforme Livrable 3 §4.3), avec suffixe
numérique en cas de collision (`sinach`, `sinach-2`, ...).

**GET /albums** : pagination + filtre `artist_id`.
**GET /albums/{id}**.
**POST /albums** [ADMIN] : `404 ARTIST_NOT_FOUND` si `artist_id`
invalide.

**GET /songs** : pagination + filtres `category_id`, `language_id`,
`artist_id`. Ne retourne que `status = PUBLISHED`.
**GET /songs/search** : `q` obligatoire (`422` sinon). Recherche par
correspondance partielle (`ILIKE`) sur `title` et `artist.name`.
**⚠️ Ne recherche PAS encore dans les paroles** — voir limitations.
**GET /songs/{slug}** : `404 SONG_NOT_FOUND` si absent ou non
`PUBLISHED` (jamais de distinction technique).
**POST /songs** [ADMIN] : `slug` généré serveur, `status` forcé à
`DRAFT` (jamais `PUBLISHED` à la création). `404` si
artist_id/album_id/category_id/original_language_id invalide.
**PUT /songs/{id}** [ADMIN] : permet notamment la transition
`DRAFT -> PUBLISHED`.

## Non implémenté (phases suivantes)

`lyrics`, `translations`, `favorites`, `admin/*` (modération) — voir
`docs/roadmap.md`.

## Écarts / limitations documentés — Phase 3

1. **Recherche** : implémentée via `ILIKE` (correspondance partielle)
   plutôt que PostgreSQL Full Text Search (`tsvector`/`GIN`) prévu en
   cible (Livrable 2 §6, Schéma directeur §12). Choix fait pour rester
   compatible avec l'environnement de test (SQLite, sans dépendance
   Postgres) et parce que l'introduction de `tsvector` est une
   amélioration incrémentale ajoutable par migration additive sans
   changer le contrat API. **Signalé comme point à valider**, pas
   tranché silencieusement comme définitif.
2. **`lyrics_available`** (prévu par les wireframes, Livrable 4) n'est
   pas encore dans `SongRead` — la table `lyrics` n'existe pas avant
   la Phase 4. Sera ajouté à ce moment, sans changement de structure
   ailleurs.
3. **CRUD partiel** : `PUT`/`DELETE` sur `artists`, `albums`,
   `categories`, `languages` ne sont pas implémentés en Phase 3 (seuls
   `GET` et `POST` où pertinent) — la Phase 3 s'est concentrée sur le
   flux de lecture/création Artists → Albums → Songs demandé
   explicitement. Ces endpoints restent dans le périmètre du Livrable
   3 et pourront être ajoutés sans rupture. **Signalé, pas un
   abandon silencieux.**
