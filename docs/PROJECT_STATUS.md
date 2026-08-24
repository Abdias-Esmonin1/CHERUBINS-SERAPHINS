# État du projet — CHERUBINS SERAPHINS

**Dernière mise à jour :** Phase 1 — Backend Foundation

## Terminé

- Cadrage complet (analyse de cadrage, MCD/MLD, architecture technique,
  spécification API, wireframes, architecture frontend) — Livrables 1 à 5.
- Modèles SQLAlchemy : `Role`, `User`, `Category`, `Language`.
- Infrastructure backend (Phase 1) :
  - Configuration (`core/config.py`, variables d'environnement).
  - Connexion PostgreSQL asynchrone (`core/database.py`).
  - Utilitaires de sécurité : hash bcrypt, JWT encode/decode
    (`core/security.py`) — pas encore branchés à des endpoints.
  - Gestion d'erreurs globale avec enveloppe JSON standard
    (`exceptions/`).
  - `main.py` fonctionnel avec `GET /health`.
  - Alembic configuré, migration initiale `0001_initial`
    (roles, categories, languages, users).
  - Suite de tests Phase 1 (8 tests, tous passants).
  - Docker : `backend/Dockerfile`, `docker-compose.yml`
    (backend + postgres + redis).

- Phase 2 — Authentication (Terminée) :
  - `POST /api/v1/auth/register`, `/login`, `/logout`, `GET /me`.
  - JWT posé exclusivement via cookie `HttpOnly` (jamais en JSON).
  - Hash bcrypt, anti-énumération sur login, gestion des comptes
    désactivés/soft-deleted.
  - `core/dependencies.py` : `get_current_user`, `require_admin`.
  - 25 tests (33 au total avec la Phase 1), tous passants.
  - Base de test : SQLite en mémoire (décision technique de test
    uniquement — aucun PostgreSQL disponible dans l'environnement
    d'implémentation ; le dev/prod restent strictement PostgreSQL).

- Phase 3 — Catalogue (Terminée) :
  - Modèles `Artist`, `Album`, `Song` (migration `0002_catalog`,
    chaînée après `0001`).
  - `GET /categories`, `/languages` (lecture publique).
  - `GET/POST /artists`, `GET /artists/{slug}` — slug généré
    serveur, jamais fourni par le client.
  - `GET/POST /albums`, `GET /albums/{id}`.
  - `GET/POST /songs`, `GET /songs/search`, `GET /songs/{slug}`,
    `PUT /songs/{id}` — statut `DRAFT` par défaut, seul `PUBLISHED`
    visible publiquement, indépendant du futur statut des paroles.
  - `require_admin` appliqué sur toutes les routes de création/mise
    à jour.
  - 25 nouveaux tests (58 au total), tous passants, 3 exécutions
    consécutives sans flakiness.
  - Limitations documentées (voir `docs/05-api/api.md`) : recherche
    par `ILIKE` plutôt que FTS PostgreSQL cible ; `lyrics_available`
    différé (voir Phase 4) ; `PUT`/`DELETE` sur artists/albums/
    categories/languages différés (hors périmètre explicite de cette
    phase, non abandonnés).

- Phase 4 — Lyrics (Terminée, portée Option A validée) :
  - Table `lyrics` (migration `0003_lyrics`, chaînée après `0002`),
    relation `Song 1--0..1 Lyrics`.
  - `POST /lyrics` (soumission, `authorization_status=PENDING` et
    `submitted_by_user_id` forcés serveur, jamais fournis par le
    client).
  - `GET /lyrics/song/{song_id}` : visibilité différenciée — public/
    autre USER (uniquement `AUTHORIZED` + non expiré), auteur (toujours
    sa propre soumission), ADMIN (toujours) — toujours `200`, jamais
    `403`/`404` pour absence de contenu.
  - `PUT /lyrics/{id}` : édition (contenu uniquement) si `PENDING`,
    par l'auteur ou l'ADMIN ; `409 LYRICS_ALREADY_REVIEWED` sinon ;
    `403` pour un tiers.
  - `GET /lyrics/mine` : soumissions propres, tous statuts, paginé,
    IDOR-safe (aucun `user_id` acceptable en paramètre).
  - `core/dependencies.py` : ajout `get_current_user_optional`
    (résolution utilisateur sans lever 401, pour endpoint public à
    réponse différenciée).
  - **Explicitement absents (Option A, réservés à la Phase 7)** :
    table `rights_records`, endpoints
    `PATCH /admin/lyrics/{id}/{authorize,reject,revoke}`, tout router
    de modération admin. Une parole soumise reste `PENDING` jusqu'à
    la Phase 7 — comportement attendu, pas une limitation cachée.
  - 32 nouveaux tests (90 au total), tous passants, stables sur 3
    exécutions consécutives. Tests de visibilité `AUTHORIZED`/
    `EXPIRED` : manipulation directe de la base (explicitement
    autorisée par la validation Option A, faute d'endpoint de
    modération à ce stade).

- Phase 5 — Translations (Terminée, portée Option A validée,
  symétrique à la Phase 4) :
  - Table `translations` (migration `0004_translations`, chaînée
    après `0003`), relation `Lyrics 1--N Translation`.
  - `POST /translations` : soumission (`USER`/`ADMIN`),
    `authorization_status`/`submitted_by_user_id` forcés serveur.
    Autorisé même si les paroles originales ne sont pas
    `AUTHORIZED` (cycles de droits indépendants).
  - `GET /translations/lyrics/{lyrics_id}` : liste avec visibilité
    déterminée indépendamment par élément (chaque traduction peut
    avoir un auteur/statut différent), filtre optionnel
    `target_language_id`.
  - `PUT /translations/{id}` : édition si `PENDING`, auteur ou ADMIN ;
    `409 TRANSLATION_ALREADY_REVIEWED` sinon ; `403` tiers.
  - `GET /translations/mine` : IDOR-safe, tous statuts, paginé.
  - **Écart documenté vs MCD initial** : `expiration_date` ajoutée à
    `Translation` (nécessaire à la règle de visibilité déjà validée
    pour les deux entités) ; `authorization_reference`/
    `authorization_date` volontairement PAS ajoutés (non requis par
    le contrat fonctionnel de cette phase).
  - **Explicitement absents (Option A, réservés à la Phase 7)** :
    `rights_records`, endpoints
    `PATCH /admin/translations/{id}/{authorize,reject,revoke}`.
  - 35 nouveaux tests (125 au total), tous passants, stables sur 3
    exécutions consécutives. Règle d'expiration vérifiée
    explicitement (3 cas côté lyrics, 2 côté translations).

- Phase 6 — Favorites (Terminée) :
  - Table `favorites` (migration `0005_favorites`, chaînée après
    `0004`), `UNIQUE(user_id, song_id)`, `ON DELETE CASCADE` sur les
    deux FK.
  - `GET/POST /favorites`, `DELETE /favorites/{song_id}` — toutes
    authentifiées, aucune route publique, aucune notion de
    droits/statut.
  - `user_id` structurellement absent du schéma de création, toujours
    `current_user.id` (IDOR-safe par construction, même principe que
    `/lyrics/mine`).
  - `DELETE` scopé strictement à `current_user` : `404
    FAVORITE_NOT_FOUND` même si le favori existe mais appartient à
    quelqu'un d'autre (jamais de `403` révélateur).
  - **Décision documentée** : aucune restriction sur `Song.status` —
    signalée comme ambiguïté avant implémentation (aucun document ne
    tranchait ce point), retenue par défaut en l'absence d'objection.
  - 21 nouveaux tests (146 au total), tous passants, stables sur 3
    exécutions consécutives.

- Phase 7 — Administration / Rights Records / Modération (Terminée) :
  - Table `rights_records` (migration `0006_rights_records`, chaînée
    après `0005`) — cible polymorphe `lyrics_id` XOR `translation_id`
    (`CHECK` d'exclusivité), append-only strict (aucun endpoint
    d'écriture, aucune méthode update/delete sur le repository).
  - **Option A validée** : `authorization_reference`/
    `authorization_date` ajoutées à `Translation` (exclues en Phase 5,
    requises maintenant par le contrat `authorize`), incluses dans la
    même migration `0006` (choix documenté : un seul changement
    fonctionnel cohérent).
  - `moderation_service.py` : logique centralisée pour `Lyrics` ET
    `Translation` — authorize (`PENDING`/`EXPIRED` → `AUTHORIZED`,
    statut *effectif* calculé comme pour la visibilité publique),
    reject (`PENDING` → `REJECTED`, `reason` obligatoire), revoke
    (`AUTHORIZED` → `REVOKED`, `reason` obligatoire). Toute transition
    hors de ces règles → `409 INVALID_TRANSITION`, sans écriture.
  - Cohérence transactionnelle stricte vérifiée explicitement par
    test dédié : une transition valide crée exactement 1
    `rights_record` ; une transition invalide n'en crée aucun.
  - 10 endpoints `/api/v1/admin/*` (lyrics, translations,
    rights-records, stats), tous protégés `require_admin`.
  - 35 nouveaux tests (181 au total), tous passants, stables sur 3
    exécutions consécutives. IDOR vérifié explicitement sur les 12
    routes admin (403 pour tout non-admin).
  - **MVP backend fonctionnel complet** (Phases 1-7).

## En cours / à faire (par phase, ordre validé)
- Phase 8 — Frontend Next.js.
- Phase 9 — Tests (couverture complète).
- Phase 10 — Docker/CI finalisation (ajout du service frontend).

## Décisions validées (rappel)

- Modèle de données MVP strict : `users, roles, categories, languages,
  artists, albums, songs, lyrics, translations, favorites,
  rights_records`.
- Hors MVP : `artist_aliases`, `lyrics_versions`, `sources` (table
  dédiée — remplacée par des champs sur `lyrics`/`translations`),
  `history`.
- Redis déclaré en infrastructure, non utilisé par le code applicatif
  en MVP.
- Pas de refresh token JWT en MVP.
- Paroles/traductions visibles publiquement uniquement si
  `authorization_status == AUTHORIZED` et non expirées — appliqué
  côté backend exclusivement.

Le détail complet des décisions est consigné dans
`docs/03-architecture/architecture.md`, `docs/04-database/database.md`
et `docs/05-api/api.md`.
