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
| `artists` | ⏳ Phase 3 — Catalogue |
| `albums` | ⏳ Phase 3 — Catalogue |
| `songs` | ⏳ Phase 3 — Catalogue |
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

## Point d'attention documenté (non résolu par du code, pour référence)

`EXPIRED` (sur `lyrics`/`translations`, tables à venir) sera calculé à
la lecture (`expiration_date < now()`), jamais écrit automatiquement
en base — pas de scheduler/Celery/cron en MVP (décision validée,
Livrable 3, arbitrage final).

Détail complet du MCD/MLD (11 tables, contraintes, index,
`rights_records` polymorphe) : voir Livrable 1 dans l'historique de
conception du projet.
