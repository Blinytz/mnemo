# Mémo

Application web personnelle de mémorisation organisée en listes thématiques.

## Fichiers principaux

- `memo.html` : application principale ;
- `manifest.json` : configuration PWA ;
- `sw.js` : service worker ;
- `thumbs/` : miniatures utilisées dans les listes ;
- `build/` : scripts de génération et de contrôle.

Les images haute définition du dossier `full/` sont conservées localement et ne
font pas encore partie du dépôt Git, afin d'éviter une archive de plusieurs
gigaoctets. Leur stratégie de stockage sera décidée séparément.

## Lancement local

Depuis la racine du projet :

```text
npx serve -l 3434 .
```

Puis ouvrir `http://localhost:3434`.

## Travail avec une IA

Codex doit lire `AGENTS.md`. Claude Code doit lire `CLAUDE.md`, qui renvoie vers
les mêmes règles communes.

