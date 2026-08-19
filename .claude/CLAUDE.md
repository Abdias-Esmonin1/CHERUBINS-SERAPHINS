# CHERUBINS SERAPHINS

## 1. IDENTITÉ DU PROJET

CHERUBINS SERAPHINS est une plateforme web dédiée à la recherche,
la consultation et l'exploitation de paroles de chants chrétiens.

L'objectif principal est de permettre à un utilisateur de retrouver
rapidement une chanson chrétienne à partir :

- de son titre ;
- de son artiste/auteur ;
- d'un extrait de paroles.

Après identification de la chanson, l'utilisateur peut consulter
les informations disponibles et accéder aux paroles lorsque celles-ci
sont disponibles et légalement utilisables.

Le projet doit évoluer progressivement vers une plateforme intelligente
intégrant notamment :

- recherche avancée ;
- recherche sémantique ;
- traduction multilingue ;
- recommandations ;
- recherche vocale ;
- autres fonctionnalités intelligentes.

---

# 2. DOCUMENTS DE RÉFÉRENCE

Les documents situés dans :

docs/

constituent les références officielles du projet.

Les documents principaux sont :

- cahier des charges ;
- schéma directeur.

Avant toute décision importante concernant :

- architecture ;
- fonctionnalités ;
- technologies ;
- base de données ;
- IA ;
- sécurité ;
- UX/UI ;

les documents de référence doivent être consultés.

En cas de contradiction entre les documents :

1. identifier la contradiction ;
2. l'expliquer ;
3. proposer une solution ;
4. demander validation avant de modifier une décision importante.

---

# 3. RÈGLE FONDAMENTALE

NE PAS COMMENCER PAR CODER.

Avant toute fonctionnalité importante :

1. comprendre le besoin ;
2. analyser l'existant ;
3. identifier les dépendances ;
4. proposer une solution ;
5. définir les fichiers concernés ;
6. implémenter ;
7. tester ;
8. vérifier les régressions ;
9. documenter.

---

# 4. PHILOSOPHIE

Le projet doit respecter :

> Construire simple → construire propre → tester → valider → améliorer.

Éviter la complexité inutile.

Ne pas ajouter une technologie uniquement parce qu'elle est populaire.

Toute technologie doit répondre à un besoin réel du projet.

---

# 5. PRINCIPES DE DÉVELOPPEMENT

Le code doit être :

- lisible ;
- modulaire ;
- maintenable ;
- testable ;
- sécurisé ;
- documenté lorsque nécessaire.

Ne jamais casser une fonctionnalité existante sans raison.

Avant une modification importante, analyser son impact.

---

# 6. IA

L'intelligence artificielle doit être intégrée progressivement.

Priorités potentielles :

1. amélioration de la recherche ;
2. recherche sémantique ;
3. traduction ;
4. recommandations ;
5. recherche vocale.

L'IA ne doit pas être utilisée lorsqu'une solution classique
est plus fiable, plus rapide ou moins coûteuse.

Une information générée par IA ne doit pas être présentée
comme officielle sans validation.

---

# 7. DROITS D'AUTEUR

Les paroles musicales peuvent être protégées par le droit d'auteur.

Le système ne doit pas être conçu pour récupérer ou republier
automatiquement des paroles protégées provenant de sources tierces
sans autorisation.

Les données relatives aux droits doivent être prises en compte
dans la conception.

Différencier notamment :

- contenu original ;
- contenu autorisé ;
- traduction officielle ;
- traduction humaine ;
- traduction générée par IA.

---

# 8. SÉCURITÉ

La sécurité doit être intégrée dès la conception.

Prendre notamment en compte :

- authentification ;
- autorisation ;
- validation des entrées ;
- gestion des secrets ;
- protection des API ;
- injection SQL ;
- XSS ;
- CSRF ;
- IDOR ;
- rate limiting ;
- contrôle des permissions.

Ne jamais stocker de secrets dans Git.

---

# 9. GIT

Utiliser Git pour le versionnement.

Branches recommandées :

main
develop
feature/*
bugfix/*

Format recommandé :

feat:
fix:
refactor:
test:
docs:
chore:

Avant chaque commit important :

- vérifier les changements ;
- exécuter les tests pertinents ;
- vérifier les secrets ;
- vérifier les régressions.

---

# 10. STRUCTURE DU PROJET

Structure principale :

.claude/
docs/
frontend/
backend/
database/
tests/
docker/

Les responsabilités doivent rester séparées.

---

# 11. DOCUMENTATION

Les décisions importantes doivent être documentées dans :

docs/

Les documents doivent rester cohérents avec l'évolution réelle
du projet.

---

# 12. MÉTHODE DE COLLABORATION AVEC L'IA

L'IA agit comme un assistant technique senior.

Elle doit :

- analyser avant d'implémenter ;
- signaler les risques ;
- proposer des alternatives ;
- expliquer les compromis ;
- éviter les suppositions importantes ;
- respecter les documents de référence ;
- tester les modifications ;
- documenter les décisions importantes.

L'IA ne doit pas simplement produire du code.
Elle doit contribuer à la conception et à la qualité globale du projet.