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

## Non implémenté (phases suivantes)

Tous les autres endpoints du Livrable 3 (`songs`, `artists`, `albums`,
`categories`, `languages`, `lyrics`, `translations`, `favorites`,
`admin/*`) — voir `docs/roadmap.md` pour l'ordre des phases.
