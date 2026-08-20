# Modèle de données — CHERUBINS SERAPHINS

**Référence :** Livrable 1 (MCD/MLD consolidé, validé).

## Entités MVP (11)

```
users, roles, categories, languages, artists, albums, songs,
lyrics, translations, favorites, rights_records
```

## Hors MVP (décision définitive)

- `artist_aliases`
- `lyrics_versions` — `lyrics` contient directement la version
  courante des paroles, pas de système de versions multiples.
- `sources` (table dédiée) — remplacée par les champs `source_type` /
  `source_url` directement sur `lyrics` et `translations`.
- `history` — schéma conceptuel seul, aucune implémentation avant V2.

## État d'implémentation

| Table | Statut |
|---|---|
| `roles` | ✅ implémentée (migration `0001_initial`) |
| `users` | ✅ implémentée (migration `0001_initial`) |
| `categories` | ✅ implémentée (migration `0001_initial`) |
| `languages` | ✅ implémentée (migration `0001_initial`) |
| `artists` | ✅ implémentée (migration `0002_catalog`) |
| `albums` | ✅ implémentée (migration `0002_catalog`) |
| `songs` | ✅ implémentée (migration `0002_catalog`) |
| `lyrics` | ⏳ Phase 4 — Lyrics |
| `translations` | ⏳ Phase 5 — Translations |
| `favorites` | ⏳ Phase 6 — Favorites |
| `rights_records` | ⏳ Phase 7 — Administration |

## Tables implémentées (Phase 1)

### roles
```
id            UUID PK
name          VARCHAR(50) UNIQUE NOT NULL   CHECK IN ('USER','ADMIN')
description   TEXT
is_active     BOOLEAN NOT NULL DEFAULT true
created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
```

### categories
```
id            UUID PK
name          VARCHAR(100) UNIQUE NOT NULL
description   TEXT
created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
```

### languages
```
id            UUID PK
code          VARCHAR(10) UNIQUE NOT NULL
name          VARCHAR(100) UNIQUE NOT NULL
native_name   VARCHAR(100)
is_active     BOOLEAN NOT NULL DEFAULT true
created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
```

### users
```
id               UUID PK
role_id          FK -> roles.id NOT NULL
email            VARCHAR(255) UNIQUE NOT NULL
password_hash    VARCHAR(255) NOT NULL
username         VARCHAR(100) UNIQUE NOT NULL
first_name       VARCHAR(150)
last_name        VARCHAR(150)
is_active        BOOLEAN NOT NULL DEFAULT true
is_verified      BOOLEAN NOT NULL DEFAULT false
avatar_url       TEXT
last_login_at    TIMESTAMPTZ
created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at       TIMESTAMPTZ    -- soft delete
```

## Tables implémentées (Phase 3)

### artists
```
id               UUID PK
name             VARCHAR(200) NOT NULL
slug             VARCHAR(220) UNIQUE NOT NULL   -- généré serveur, jamais fourni par le client
biography        TEXT
country          VARCHAR(100)
image_url        TEXT
official_links   JSONB (JSON générique hors PostgreSQL — voir note technique)
is_verified      BOOLEAN NOT NULL DEFAULT false
created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at       TIMESTAMPTZ    -- soft delete (non exploité par un endpoint DELETE en Phase 3, voir limitations)
```

### albums
```
id            UUID PK
artist_id     FK -> artists.id NOT NULL   ON DELETE RESTRICT
title         VARCHAR(255) NOT NULL
release_year  SMALLINT
cover_url     TEXT
created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
```

### songs
```
id                       UUID PK
title                    VARCHAR(255) NOT NULL
slug                     VARCHAR(280) UNIQUE NOT NULL   -- généré serveur
artist_id                FK -> artists.id NOT NULL       ON DELETE RESTRICT
album_id                 FK -> albums.id                  ON DELETE SET NULL
category_id              FK -> categories.id               ON DELETE RESTRICT
original_language_id     FK -> languages.id NOT NULL        ON DELETE RESTRICT
cover_url                TEXT
status                   VARCHAR(20) NOT NULL DEFAULT 'DRAFT'
                         CHECK IN ('DRAFT','PUBLISHED','ARCHIVED')
external_provider        VARCHAR(50)
external_id              VARCHAR(255)
external_url             TEXT
created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
deleted_at               TIMESTAMPTZ    -- soft delete (non exploité par un endpoint DELETE en Phase 3)
```
Une chanson `DRAFT`/`ARCHIVED` n'est jamais retournée par les endpoints
publics (`GET /songs`, `/songs/search`, `/songs/{slug}`) — seul
`PUBLISHED` est visible publiquement. Indépendant du statut des
paroles (`lyrics`, Phase 4).

### Note technique — `official_links`

Le MCD (Livrable 1) prévoit `JSONB` (PostgreSQL). Le modèle utilise
`JSON().with_variant(JSONB(), "postgresql")` : JSONB en production,
JSON générique sur les moteurs sans support JSONB (utilisé
uniquement par la base de test SQLite en mémoire — voir
`tests/conftest.py`). Aucun impact sur le contrat API.

## Point d'attention documenté (non résolu par du code, pour référence)

`EXPIRED` (sur `lyrics`/`translations`, tables à venir) sera calculé à
la lecture (`expiration_date < now()`), jamais écrit automatiquement
en base — pas de scheduler/Celery/cron en MVP (décision validée,
Livrable 3, arbitrage final).

Détail complet du MCD/MLD (11 tables, contraintes, index,
`rights_records` polymorphe) : voir Livrable 1 dans l'historique de
conception du projet.
