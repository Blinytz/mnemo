# Mémo — consignes de travail

## Profil du propriétaire

Le propriétaire du projet ne code pas. Expliquer les actions en français simple,
prendre en charge les opérations techniques lorsque c'est possible et demander une
validation avant toute action irréversible, publication ou modification de données
distantes.

## Application

- Application web personnelle installable (PWA).
- Point d'entrée principal : `memo.html`.
- Manifest : `manifest.json`.
- Service worker : `sw.js`.
- Miniatures utilisées par l'application : `thumbs/`.
- Images haute définition : `full/` (conservées localement et exclues de Git pour
  le moment).
- Scripts de construction et de contrôle : `build/`.
- Données éditoriales complémentaires : `data/`.

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
- Ne pas ajouter `build/.cache.pkl`, `full/`, les journaux ou les livrables générés.
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

