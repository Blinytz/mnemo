# Mémo — consignes de travail

## Profil du propriétaire

Le propriétaire du projet ne code pas. Expliquer les actions en français simple,
prendre en charge les opérations techniques lorsque c'est possible et demander une
validation avant toute action irréversible, publication ou modification de données
distantes.

## Application

- Application web personnelle installable (PWA).
- Point d'entrée : `app/` (nouvelle version) ; `memo.html` garde l'ancienne version et la source des listes.
- Manifest : `manifest.json`.
- Service worker : `sw.js`.
- Miniatures utilisées par l'application : `thumbs/`.
- Images haute définition : `full/` (seuls les fichiers utilisés sont versionnés,
  ajoutés avec `git add -f` ; le dossier reste ignoré).
- Adresse officielle : <https://blinytz.github.io/memo/> (publication
  automatique à chaque envoi sur `main`). `memo-web` n'est plus qu'une
  redirection.
- Scripts de construction et de contrôle : `build/`.
- Données éditoriales complémentaires : `data/`.

## Nouvelle version (app/), officielle depuis le 01/10/2026

- L'adresse officielle <https://blinytz.github.io/memo/> ouvre `app/` (index.html,
  manifeste, et `memo.html` qui redirige). Détails : `app/LISEZMOI.md`.
- `memo.html` reste dans le dépôt et reste **la source des listes** : l'Atelier
  (local et en ligne) et le générateur WikiDeck y écrivent. L'ancienne version
  s'ouvre encore avec `memo.html?ancienne`.
- Les données de `app/` (`data/catalogue.json`, `data/listes/<id>.json`) sont
  refaites **à chaque publication** par le workflow (`build/exporter_donnees.mjs`).
  En local, relancer `node build/exporter_donnees.mjs` après un lot WikiDeck pour
  tester et pour versionner les liens Wikipédia (le workflow n'a pas le dossier
  WikiDeck : il reprend les liens déjà présents dans `data/`).
- Le workflow écrit `version.json` (numéro de commit) : l'application installée
  le relit au retour au premier plan et se recharge d'elle-même.
- Éclats : seul le quiz du jour en rapporte ; l'utilisateur les verse dans le
  registre commun (`eclats_reward`, app_id `memo`, clé `memo-quiz-AAAA-MM-JJ`).
- Décisions du propriétaire, à ne pas rediscuter : 20 questions au quiz du jour,
  barème réglable par l'utilisateur (par défaut 0 à 9 : 0 · 10 à 12 : 10 ·
  13 à 15 : 25 · 16 ou 17 : 45 · 18 ou 19 : 75 · 20 : 120) ; les révisions ne
  rapportent rien ; pas de propositions, les réponses sont tapées ; le verdict
  peut toujours être renversé ; liens Wikipédia pour approfondir.
- Les modifications de listes faites dans l'application restent sur l'appareil
  (couche par-dessus les listes officielles) ; les corrections destinées à tous
  passent par WikiDeck ou l'Atelier.
- Tests : `node --test "app/tests/*.test.mjs"`.
- `maquette.html` n'est plus qu'une redirection vers `app/`.

## Lancement local

Servir la racine du projet avec un serveur HTTP local. Configuration historique :

```text
npx serve -l 3434 .
```

Ne jamais ouvrir simplement `memo.html` en `file://` pour valider le service worker.

## Vérifications minimales

Après une modification fonctionnelle :

1. lancer l'application sur un serveur local ;
2. vérifier l'absence d'erreurs importantes dans la console ;
3. vérifier l'ouverture de l'écran principal ;
4. vérifier au moins une liste et l'affichage de ses miniatures ;
5. signaler clairement les vérifications non réalisables.

## Sécurité et Git

- Ne jamais enregistrer de clé API, mot de passe, jeton ou fichier `.env` dans Git.
- Ne pas versionner `.claude/settings.local.json`.
- Ne pas ajouter `build/.cache.pkl`, les brouillons de `full/`, les journaux ou
  les livrables générés.
- Ne jamais publier ou pousser vers GitHub sans accord explicite du propriétaire.
- Une seule IA modifie ce dossier à la fois.
- Avant de modifier, lire l'état Git et préserver les changements existants.
- Faire des changements petits et explicables.

## Transmission entre IA

À la fin d'une intervention, résumer :

- l'objectif demandé ;
- les fichiers modifiés ;
- les vérifications effectuées ;
- les problèmes restants ;
- la prochaine action recommandée.

Le projet ne partage actuellement aucune donnée liée à la monnaie virtuelle
« éclats ». Ne pas introduire cette intégration sans demande explicite.

