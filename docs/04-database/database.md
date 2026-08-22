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
| `lyrics` | ✅ implémentée (migration `0003_lyrics`) |
| `translations` | ✅ implémentée (migration `0004_translations`) |
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

## Tables implémentées (Phase 4)

### lyrics
```
id                       UUID PK
song_id                  FK -> songs.id UNIQUE NOT NULL   ON DELETE RESTRICT
language_id              FK -> languages.id NOT NULL       ON DELETE RESTRICT
content                  TEXT NOT NULL
source_type              VARCHAR(20) NOT NULL
                         CHECK IN ('ORIGINAL','ARTIST','RIGHTS_HOLDER',
                                   'LICENSE','PARTNER','PUBLIC_DOMAIN',
                                   'USER_SUBMITTED')
source_url               TEXT
rights_holder            VARCHAR(255)
authorization_status     VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                         CHECK IN ('PENDING','AUTHORIZED','REJECTED',
                                   'EXPIRED','REVOKED')
authorization_reference  VARCHAR(100)
authorization_date       DATE
expiration_date          DATE
submitted_by_user_id     FK -> users.id                    ON DELETE SET NULL
reviewed_by_user_id      FK -> users.id                     ON DELETE SET NULL
created_at               TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at               TIMESTAMPTZ NOT NULL DEFAULT now()
```
Relation `Song 1 -- 0..1 Lyrics` (une seule ligne par chanson, pas de
versions). `submitted_by_user_id`/`authorization_status` toujours
forcés côté serveur, jamais fournis par le client.

**Portée Phase 4 (Option A, validée)** : `rights_records` et les
endpoints de modération (`PATCH .../authorize|reject|revoke`)
n'existent PAS dans cette phase — explicitement réservés à la
**Phase 7 — Administration**. Une parole soumise reste donc `PENDING`
jusqu'à l'implémentation de cette phase ultérieure. Ce n'est pas un
oubli : c'est la portée validée.

## Tables implémentées (Phase 5)

### translations
```
id                     UUID PK
lyrics_id              FK -> lyrics.id NOT NULL              ON DELETE RESTRICT
target_language_id     FK -> languages.id NOT NULL             ON DELETE RESTRICT
content                TEXT NOT NULL
translation_type       VARCHAR(20) NOT NULL
                       CHECK IN ('OFFICIAL','AUTHOR','HUMAN','AI_GENERATED')
authorization_status   VARCHAR(20) NOT NULL DEFAULT 'PENDING'
                       CHECK IN ('PENDING','AUTHORIZED','REJECTED',
                                 'EXPIRED','REVOKED')
expiration_date        DATE
source_url             TEXT
rights_holder          VARCHAR(255)
submitted_by_user_id   FK -> users.id                          ON DELETE SET NULL
reviewed_by_user_id    FK -> users.id                           ON DELETE SET NULL
created_at             TIMESTAMPTZ NOT NULL DEFAULT now()
updated_at             TIMESTAMPTZ NOT NULL DEFAULT now()
UNIQUE(lyrics_id, target_language_id)
```
Relation `Lyrics 1 -- N Translation` (plusieurs langues cibles
possibles). Cycle de droits totalement indépendant de
`Lyrics.authorization_status` — une traduction peut être `AUTHORIZED`
alors que l'original ne l'est pas, et inversement.
`submitted_by_user_id`/`authorization_status` toujours forcés côté
serveur.

**Écart documenté par rapport au MCD initial (Livrable 1)** :
`expiration_date` a été ajoutée à `translations` bien que le MCD
initial ne la mentionnait pas — nécessaire pour appliquer la règle de
visibilité déjà validée (`AUTHORIZED` + non expiré), qui s'applique
explicitement aux deux entités. **`authorization_reference` et
`authorization_date` n'ont volontairement PAS été ajoutés** : rien
dans le contrat fonctionnel/API de la Phase 5 ne les requiert, et leur
ajout par simple symétrie avec `Lyrics` a été explicitement exclu par
consigne.

**Portée Phase 5 (Option A, symétrique à la Phase 4)** : `rights_records`
et les endpoints de modération n'existent PAS dans cette phase —
réservés à la **Phase 7 — Administration**. Une traduction soumise
reste `PENDING` jusqu'à cette phase.

## Point d'attention documenté (non résolu par du code, pour référence)

`EXPIRED` (sur `lyrics` et `translations`, toutes deux implémentées)
est calculé à
la lecture (`expiration_date < now()`), jamais écrit automatiquement
en base — pas de scheduler/Celery/cron en MVP (décision validée,
Livrable 3, arbitrage final).

Détail complet du MCD/MLD (11 tables, contraintes, index,
`rights_records` polymorphe) : voir Livrable 1 dans l'historique de
conception du projet.
