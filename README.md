# Mémo

Application web personnelle de mémorisation organisée en listes thématiques.

## Fichiers principaux

- `memo.html` : application principale ;
- `manifest.json` : configuration PWA ;
- `sw.js` : service worker ;
- `thumbs/` : miniatures utilisées dans les listes ;
- `build/` : scripts de génération et de contrôle.

Adresse officielle : <https://blinytz.github.io/memo/>, publiée par
`.github/workflows/deploy-pages.yml` à chaque envoi sur `main`. L'Atelier en
ligne est à <https://blinytz.github.io/memo/atelier.html>.

Les images haute définition de `full/` (et les originaux de `originaux/`) qui
sont utilisées par l'application sont versionnées ; les deux dossiers restent
ignorés par Git pour ne pas embarquer les brouillons locaux (ajout avec
`git add -f`).

## Lancement local

Depuis la racine du projet :

```text
npx serve -l 3434 .
```

Puis ouvrir `http://localhost:3434`.

## Travail avec une IA

Codex doit lire `AGENTS.md`. Claude Code doit lire `CLAUDE.md`, qui renvoie vers
les mêmes règles communes.

