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

`admin/*` (modération, `rights_records`) — voir `docs/roadmap.md`.

## Implémenté — Phase 4 (Lyrics)

```
POST /api/v1/lyrics
GET  /api/v1/lyrics/mine
GET  /api/v1/lyrics/song/{song_id}
PUT  /api/v1/lyrics/{lyrics_id}
```

**⚠️ Portée Phase 4 = Option A (validée)** : aucune transition de
statut n'est possible via l'API dans cette phase. Les endpoints
`PATCH /admin/lyrics/{id}/{authorize,reject,revoke}` et la table
`rights_records` appartiennent explicitement à la **Phase 7 —
Administration**. Une parole soumise reste `PENDING` jusqu'à
l'implémentation de cette phase — ce n'est pas un oubli, c'est la
portée validée.

**POST /lyrics** : auth requise (`USER`/`ADMIN`). Body `{song_id,
language_id, content, source_type, source_url?, rights_holder?}` —
`submitted_by_user_id` et `authorization_status` structurellement
absents du schéma d'entrée, forcés côté serveur (`PENDING`, utilisateur
courant). Erreurs : `404 SONG_NOT_FOUND`, `404 LANGUAGE_NOT_FOUND`,
`409 LYRICS_ALREADY_EXISTS` (une seule ligne `lyrics` par chanson),
`422` (source_type hors énumération).

**GET /lyrics/song/{song_id}** : public (authentification optionnelle).
Toujours `200`, jamais `403`/`404` pour une absence de contenu (évite
l'énumération de l'état des droits) :
```
Visiteur public / autre USER : {available: bool, language?, content?}
                                — uniquement si AUTHORIZED et
                                  (expiration_date IS NULL OR
                                   expiration_date >= aujourd'hui)
Auteur (submitted_by_user_id == current_user.id) : vue enrichie
                                complète, quel que soit le statut
ADMIN : vue enrichie complète, quel que soit le statut
```
`404 SONG_NOT_FOUND` uniquement si `song_id` ne référence aucune
chanson (indépendant de `Song.status`).

**PUT /lyrics/{id}** : auteur (si `authorization_status = PENDING`
uniquement) ou `ADMIN` (même restriction `PENDING` — voir décision
ci-dessous). Body limité à `{content?, source_url?, rights_holder?}` ;
`song_id`, `language_id`, `source_type`, `submitted_by_user_id`,
`authorization_status`, `reviewed_by_user_id` structurellement absents.
Erreurs : `404 LYRICS_NOT_FOUND`, `403` (tiers), `409
LYRICS_ALREADY_REVIEWED` (statut ≠ `PENDING`).

**GET /lyrics/mine** : auth requise. Retourne uniquement les
soumissions de `current_user`, tous statuts, paginé — aucun `user_id`
acceptable en paramètre (protection IDOR par construction).

### Décision d'interprétation documentée (Phase 4)

La restriction "édition uniquement si `PENDING`" s'applique **à
l'auteur ET à l'ADMIN** de façon identique sur `PUT /lyrics/{id}`,
conformément au contrat initial du Livrable 3 §8.3 ("Un ADMIN ou
l'auteur... peut corriger... tant que `authorization_status =
PENDING`"). Cet endpoint ne gère que l'édition de contenu — les
actions de modération de la Phase 7 (`authorize`/`reject`/`revoke`)
seront un mécanisme distinct, non soumis à cette même restriction.

## Implémenté — Phase 5 (Translations)

```
POST /api/v1/translations
GET  /api/v1/translations/mine
GET  /api/v1/translations/lyrics/{lyrics_id}
PUT  /api/v1/translations/{translation_id}
```

**⚠️ Portée Phase 5 = Option A (symétrique à la Phase 4, validée)** :
aucune transition de statut n'est possible via l'API. Les endpoints
`PATCH /admin/translations/{id}/{authorize,reject,revoke}` et la table
`rights_records` appartiennent explicitement à la **Phase 7**. Une
traduction soumise reste `PENDING` jusqu'à cette phase.

**POST /translations** : auth requise (`USER`/`ADMIN`). Body
`{lyrics_id, target_language_id, content, translation_type,
source_url?, rights_holder?}` — `submitted_by_user_id` et
`authorization_status` structurellement absents, forcés côté serveur.
**Autorisé même si les paroles originales (`lyrics_id`) ne sont pas
elles-mêmes `AUTHORIZED`** — cycles de droits indépendants (décision
validée). Erreurs : `404 LYRICS_NOT_FOUND`, `404 LANGUAGE_NOT_FOUND`,
`409 TRANSLATION_ALREADY_EXISTS` (`UNIQUE(lyrics_id,
target_language_id)`), `422`.

**GET /translations/lyrics/{lyrics_id}** : public (authentification
optionnelle). Retourne une **liste** (une entrée par langue cible
ayant une traduction soumise), avec visibilité déterminée
**indépendamment pour chaque élément** — deux traductions d'une même
parole peuvent avoir des auteurs et statuts différents :
```
Visiteur public / autre USER : {available: bool, target_language,
                                 translation_type?, content?}
                                — translation_type/content omis si
                                  available=false
Auteur (de CETTE traduction)  : vue enrichie complète
ADMIN                          : vue enrichie complète
```
Filtre optionnel `?target_language_id=...`. `404 LYRICS_NOT_FOUND` si
`lyrics_id` invalide. Toujours `200` pour l'absence de contenu (jamais
`403`/`404`).

**PUT /translations/{id}** : auteur (si `PENDING` uniquement) ou
`ADMIN` (même restriction — décision d'interprétation identique à
celle retenue pour `Lyrics`, Phase 4). Body limité à `{content?,
source_url?, rights_holder?}`. Erreurs : `404
TRANSLATION_NOT_FOUND`, `403` (tiers), `409
TRANSLATION_ALREADY_REVIEWED`.

**GET /translations/mine** : auth requise. Soumissions propres, tous
statuts, paginé, IDOR-safe.

### Écart documenté avec le MCD initial (Phase 5)

Le modèle `Translation` inclut `expiration_date` (absent du MCD
initial du Livrable 1), nécessaire pour appliquer la règle de
visibilité déjà validée pour les deux entités. `authorization_reference`
et `authorization_date` n'ont volontairement PAS été ajoutés par
simple symétrie avec `Lyrics` — aucune exigence fonctionnelle/API ne
les requiert en Phase 5.

## Implémenté — Phase 6 (Favorites)

```
GET    /api/v1/favorites
POST   /api/v1/favorites
DELETE /api/v1/favorites/{song_id}
```

Aucune notion de droits/statut — toutes les routes exigent
l'authentification, aucune n'est publique. Aucun endpoint de
modération (`Favorite` ne possède pas de cycle de droits).

**GET /favorites** : auth requise. Retourne uniquement les favoris de
`current_user`, paginé. Chaque élément inclut la fiche complète de la
chanson (`SongRead`, réutilisé tel quel).

**POST /favorites** : auth requise. Body `{song_id}` — `user_id`
structurellement absent, toujours `current_user.id`. Erreurs :
`404 SONG_NOT_FOUND`, `409 ALREADY_FAVORITED`
(`UNIQUE(user_id, song_id)`).

**DELETE /favorites/{song_id}** : auth requise. Supprime uniquement le
favori appartenant à `current_user` (recherche scopée
`WHERE user_id = current_user.id AND song_id = {id}` — protection
IDOR explicite). `404 FAVORITE_NOT_FOUND` si l'utilisateur n'a pas ce
favori, y compris si le favori existe mais appartient à quelqu'un
d'autre (jamais de `403` qui révélerait l'existence du favori
d'autrui).

### Décision documentée (Phase 6)

Aucune restriction sur `Song.status` pour `POST /favorites` — une
chanson `DRAFT`/`ARCHIVED` peut être ajoutée aux favoris si son UUID
est connu. Signalé comme ambiguïté avant implémentation (aucun
document ne tranchait ce point), retenu par défaut en l'absence
d'objection explicite. Voir `docs/04-database/database.md`.

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
   toujours pas dans `SongRead` — la table `lyrics` existe désormais
   (Phase 4), mais l'ajout de ce champ nécessiterait de modifier
   `SongRead`/`catalog_service.py` (Phase 3), ce qui n'était pas dans
   le périmètre annoncé de la Phase 4. Reste possible sans rupture,
   non fait ici pour respecter strictement la liste de fichiers
   annoncée.
3. **CRUD partiel** : `PUT`/`DELETE` sur `artists`, `albums`,
   `categories`, `languages` ne sont pas implémentés en Phase 3 (seuls
   `GET` et `POST` où pertinent) — la Phase 3 s'est concentrée sur le
   flux de lecture/création Artists → Albums → Songs demandé
   explicitement. Ces endpoints restent dans le périmètre du Livrable
   3 et pourront être ajoutés sans rupture. **Signalé, pas un
   abandon silencieux.**
