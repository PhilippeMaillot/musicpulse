# Plan de présentation — MusicPulse

Équipe : Philippe Maillot, Erwan Marchand et Evan Afonso.

## Message principal

MusicPulse est un cas d'étude destiné à expliquer la complémentarité de deux technologies NoSQL validées par le formateur :

- Cloud Firestore pour les documents durables, indexés et sécurisés ;
- Redis pour les données rapides, temporaires et spécialisées.

La recommandation musicale illustre les technologies, mais ne constitue pas l'objectif central du TP.

## Déroulé proposé — 20 minutes

### 1. Contexte et dataset — 3 minutes

- problématique technique ;
- présentation du dataset Kaggle ;
- volume : 50 683 morceaux, 9,7 millions d'interactions et 962 037 utilisateurs ;
- problèmes de qualité, notamment les genres manquants ;
- nettoyage et création de `primary_genre`.

### 2. Firestore — 5 minutes

- différence entre Firebase et Cloud Firestore ;
- collections et documents ;
- modèle dénormalisé d'un morceau ;
- index simples et composés ;
- démonstration Create, Read, Update, Delete ;
- règles de sécurité et authentification ;
- import massif, sauvegarde et restauration.

### 3. Redis — 5 minutes

- fonctionnement en mémoire ;
- String pour une fiche en cache ;
- Hash pour les compteurs ;
- List pour les dernières écoutes ;
- Sorted Set pour les classements ;
- TTL et expiration automatique ;
- persistance AOF et sécurisation du service.

### 4. Complémentarité — 4 minutes

- Firestore comme source de vérité ;
- Redis comme accélérateur ;
- démonstration du cache-aside ;
- comparaison cache miss/cache hit ;
- invalidation du cache après une modification ;
- compromis cohérence, coût et performance.

### 5. WebApp et conclusion — 3 minutes

- tableau de bord analytique ;
- recherche dans le catalogue ;
- recommandation par caractéristiques audio ;
- synthèse des avantages et limites des deux technologies.

## Démonstration en direct

1. Ouvrir un document Firestore.
2. Ajouter un morceau depuis la WebApp.
3. Le modifier puis le supprimer.
4. Lire une fiche avec un cache Redis vide.
5. Observer la création de la clé et son TTL.
6. Relire la fiche et montrer le cache hit.
7. Simuler plusieurs écoutes.
8. Afficher la List des dernières écoutes et le Sorted Set du classement.
9. Présenter les règles Firestore et les scripts d'administration.

## Questions auxquelles être préparés

- Pourquoi ne pas tout stocker dans Firestore ?
- Pourquoi Redis n'est-il pas la source de vérité ?
- Comment éviter un cache obsolète ?
- Comment les données sont-elles dénormalisées ?
- Quels index ont été créés et pourquoi ?
- Que se passe-t-il si Redis tombe ?
- Comment sauvegarder et restaurer les données ?
- Comment empêcher un utilisateur de modifier le catalogue ?

