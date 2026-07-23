# Build — Images locales pour Mémo

## Lancer le build

```bash
cd build
set TMDB_API_KEY=votre_clé_ici
python build_images.py
```

Le script est rejouable : il ne retélécharge pas les images déjà présentes dans `thumbs/` et `full/`.

## Options

| Option | Description |
|--------|-------------|
| `--force` | Retélécharger toutes les images (ignore le cache) |
| `--list films` | Traiter une seule liste (utile pour corriger des manquants) |
| `--no-patch` | Ne pas modifier `memo.html` (téléchargement seul) |
| `--verify-only` | Vérification de couverture sans téléchargement |

## Corriger un manquant manuellement

1. Ouvrir `rapport_manquants.csv`
2. Repérer la ligne (liste + numéro de ligne)
3. Placer manuellement l'image dans `thumbs/<liste>/<n>.webp` et `full/<liste>/<n>.webp`
4. Relancer `python build_images.py --list <id_liste>` pour mettre à jour `memo.html`

## Structure générée

```
repo/
├── memo.html              ← app patchée (chemins locaux)
├── thumbs/<liste>/<n>.webp  ← miniatures 160 px de haut
├── full/<liste>/<n>.webp    ← zoom 800 px max
└── build/
    ├── build_images.py    ← ce script
    ├── extract_data.js    ← extracteur Node.js
    ├── manifest.json      ← liste/ligne/col → fichier + source
    ├── rapport_manquants.csv
    └── .cache.pkl         ← cache HTTP (supprimer pour forcer)
```

## Notes

- `peintres` : le portrait est `<n>.webp`, l'image de l'œuvre est `<n>b.webp`
- `pays` et `departements` : fichiers `.svg` (pas de conversion)
- `elements` : data-URI SVG inline (aucun fichier généré)
- `etats_usa` : drapeaux SVG depuis Wikimedia Commons
