# PROMPT — Mémo : miniatures locales définitives (build hybride)

> À exécuter avec Claude Code, depuis le dossier du repo GitHub Pages contenant
> `memo_v46_images.html`. Connexion Internet requise (une seule fois, pour le build).
> Prérequis : une clé API TMDB gratuite (themoviedb.org → Paramètres → API) dans
> la variable d'environnement `TMDB_API_KEY`. Si absente, demander avant de
> commencer ; en dernier recours seulement, basculer les films sur en.wikipedia.

---

## Contexte

Mémo est une PWA mono-fichier (HTML/CSS/JS, localStorage) de mémorisation de
listes, déployée sur GitHub Pages. 23 listes, ~1 850 lignes. Chaque liste a une
colonne `Image` (index 1), la liste `peintres` a une seconde colonne image
(`Image œuvre`). Toutes les tentatives de résolution d'images **au runtime**
(API à l'affichage) ont échoué : lenteur, quotas, URLs cassées, mauvaises
correspondances. Usage strictement personnel : les images non libres de droit
(affiches, art de jeu vidéo, couvertures) sont acceptées et même préférées
quand elles sont plus parlantes.

## Objectif — non négociable

Les miniatures s'affichent **instantanément (<1 s), pour toutes les lignes de
toutes les listes, sans aucune requête externe au runtime**. Un clic sur la
ligne ouvre une version grande du **même** visuel. Le résultat doit être
**vérifié par le script**, pas supposé.

## Architecture cible

```
repo/
├── memo.html                      ← app patchée (données pointent vers thumbs/)
├── thumbs/<liste>/<n>.webp        ← miniatures 160 px de haut (~3-8 Ko)
├── full/<liste>/<n>.webp          ← version zoom 800 px max
└── build/
    ├── build_images.py            ← le script de build (rejouable)
    ├── manifest.json              ← liste/ligne/colonne → fichier + source + titre
    └── rapport_manquants.csv      ← lignes sans image, avec cause
```

## Étapes

### 1. Extraction
Parser `DEFAULT_LISTS` dans le HTML. Pour chaque liste, identifier toutes les
colonnes image (nom contenant image/photo/portrait/drapeau/illustration/icone/
visuel) et le libellé de référence de chaque cellule image :
- colonne 1 : la colonne définie dans `IMAGE_REFERENCE_COLUMNS` (déjà dans le code) ;
- colonne secondaire (ex. `Image œuvre`) : la colonne texte précédente
  (`Œuvre principale`).

### 2. Résolution — source par liste

Chaque succès doit être **vérifié** : téléchargement HTTP 200 + image décodable
par Pillow. Sinon, passer à la source suivante de la chaîne.

**Choix de source imposés (cohérence visuelle voulue par l'utilisateur) :**

- **`mythologie`** : l'illustration par défaut de CHAQUE personnage est l'art
  officiel des jeux **Hades / Hades II** (hades.fandom.com). Ordre :
  1. `HADES_OFFICIAL_FILES` du HTML →
     `https://hades.fandom.com/wiki/Special:Redirect/file/<fichier>` ;
  2. personnages absents de cette table : API du wiki
     (`hades.fandom.com/api.php`, `generator=search` + `pageimages`) avec le nom
     anglais de `WIKI_IMAGE_ALIASES`, en privilégiant les pages dont le titre
     correspond exactement au personnage ;
  3. en dernier recours seulement (personnage absent des deux jeux) :
     Wikipédia en/fr (statue ou peinture classique).
  Télécharger avec un User-Agent navigateur ; si Fandom renvoie 403, récupérer
  l'URL `static.wikia.nocookie.net` via l'API (`prop=imageinfo&iiprop=url`).
  Ne pas mentionner la provenance dans l'interface : c'est simplement
  l'illustration choisie.

- **`departements`** : l'image par défaut est la **carte de localisation
  Wikimedia Commons** (département en rouge sur la France en bleu), pour la
  cohérence visuelle de toute la liste. Ordre :
  1. `Special:FilePath/<Nom>-Position.svg`, en testant les variantes de nommage
     connues (apostrophes typographiques `’` vs `'`, tirets, `Corse-du-Sud`,
     `Côtes-d'Armor`, etc.) ;
  2. si introuvable : API Commons, recherche
     `<Nom> département position locator map France` dans le namespace File,
     en ne retenant qu'un SVG/PNG dont le nom contient `Position` ou
     `locator map` (pour rester dans le même style rouge/bleu) ;
  3. consigner tout département résolu hors style « Position » dans le rapport,
     pour correction manuelle.

- **`films` (390 lignes)** : **TMDB**. `GET /search/movie` avec
  `query=<Titre>&year=<Année>&language=fr-FR` ; si 0 résultat, retenter sans
  `year`, puis avec le nom du réalisateur retiré du titre des homonymes via
  `/movie/{id}/credits` pour départager. Affiche :
  `https://image.tmdb.org/t/p/w342<poster_path>` (thumb) et `w780` (full).
  Repli : en.wikipedia titre exact, puis recherche.

- **`litterature`** : **Open Library Covers** (sans clé) :
  `https://covers.openlibrary.org/b/$KEY/$VALUE-M.jpg` après
  `openlibrary.org/search.json?title=<Titre>&author=<Auteur>` (tester le titre
  français puis le titre original si échec). Repli : Google Books API
  (`volumes?q=intitle:<Titre>+inauthor:<Auteur>`, champ `imageLinks`), puis
  Wikipédia.

- **`elements`** : conserver les tuiles SVG stylisées existantes (data-URI,
  déjà instantanées et cohérentes). Ne pas chercher de photo.

- **`pays`** : drapeaux `flagcdn.com` via `flagCodeMap` (télécharger les SVG en
  local). **`etats_usa`** : URLs Commons déjà présentes dans les données.
  **`philosophes`** : `PHILOSOPHER_COMMONS_FILES` du HTML, repli Wikipédia.

- **Toutes les autres listes** (rois, chefs d'État, peintres + œuvres, os,
  guerres, événements XIXe/XXe, mouvements, JO, coupes du monde, F1, consoles,
  lunes, périodes géologiques) : **Wikipédia par lots** —
  `action=query&prop=pageimages&piprop=thumbnail|original&pithumbsize=320&redirects=1`,
  lots de 50 titres. Candidats par liste : reprendre `imgCandidateTitlesForRow`
  du HTML (départements `X (département)` n'est plus utile ici ; lunes
  `X (lune)` ; coupes du monde `Coupe du monde de football [de] YYYY` ; JO
  `Jeux olympiques d'été/d'hiver de YYYY` ; alias `WIKI_IMAGE_ALIASES`).
  Ordre : fr titre exact → en titre exact → recherche plein texte fr puis en
  (`generator=search`, première page avec image, requête = libellé + contexte
  de `IMAGE_REFERENCE_COLUMNS`).

- **Filet final toutes listes** (résidus après tout ça) : si une clé
  `GOOGLE_CSE_KEY`/`GOOGLE_CSE_CX` est fournie, Google Custom Search Images
  (max 100/jour) avec requête libellé + contexte ; sinon laisser vide et
  documenter. Échec définitif → `rapport_manquants.csv` (liste, n° ligne,
  libellé, requêtes tentées, cause).

Politesse API : lots quand l'API le permet, ~200 ms entre requêtes, User-Agent
identifié, retry sur 429, cache disque des réponses (le build doit être
rejouable sans tout retélécharger).

### 3. Téléchargement et conversion
Pour chaque succès : produire avec Pillow `thumbs/<liste>/<n>.webp` (160 px de
haut, qualité 80) et `full/<liste>/<n>.webp` (max 800 px). SVG (drapeaux,
cartes de départements) : copier tel quel en `.svg` dans les deux dossiers.
Nommage : index de ligne, suffixe `b` pour la colonne secondaire
(`peintres/12b.webp`).

### 4. Patch du HTML → `memo.html`
- Écrire les chemins relatifs (`thumbs/peintres/12.webp`) dans les cellules
  image de `DEFAULT_LISTS`, et le chemin `full/...` + titre/source dans un
  nouveau champ `imageFiles` par liste (consommé par le zoom du modal).
- **Supprimer toute résolution réseau au runtime** : `resolveListImages`,
  `wikiBatchImageQuery`, `wikiSearchImageQuery`, auto-résolution. Garder le
  bouton « Image Wikipédia » du modal d'édition (action manuelle ponctuelle)
  et l'upload.
- **Migration localStorage v47 (critique — cause de la régression actuelle)** :
  au chargement, pour chaque liste par défaut stockée, remplacer la valeur de
  chaque cellule image par le chemin local du build (correspondance par id de
  liste + index de ligne, vérifiée par le libellé de référence ; en cas de
  désaccord, correspondance par libellé). Les images **uploadées par
  l'utilisateur** (`data:image/`, hors SVG génériques « à enrichir ») sont
  conservées. Purger les anciens `imageMeta` et tous les placeholders.
- Zoom modal : ouvrir le `full/...` correspondant. `loading="lazy"` sur les
  `<img>` du tableau, `handleImageError` conservé en dernier filet.

### 5. Vérification automatique — à exécuter et afficher
1. **Couverture** : cellules image avec fichier local existant / total, par
   liste. Objectif ≥ 98 % global ; tout manquant listé dans le CSV.
2. **Cohérence de style** : 100 % des `mythologie` proviennent de
   hades.fandom/wikia (sauf exceptions documentées) ; 100 % des `departements`
   sont des cartes « Position » (sauf exceptions documentées).
3. **Intégrité** : chaque chemin écrit dans `memo.html` correspond à un fichier
   présent et lisible ; chaque thumb a son `full`.
4. **Zéro réseau** : grep dans `memo.html` — aucune URL
   `wikipedia|wikimedia|fandom|flagcdn|tmdb|openlibrary` dans les cellules de
   données ni dans le rendu du tableau (tolérées uniquement dans le module
   « Image Wikipédia » du modal).
5. **Boot test** (Node + jsdom, fetch mocké pour échouer) : l'app démarre sans
   erreur, les 23 listes s'affichent, ouvrir `peintres`, `films`, `mythologie`,
   `departements`, `pays` rend un `<img>` local pour chaque cellule image,
   zéro appel fetch.
6. **Poids** : taille totale `thumbs/` + `full/` (cible < 60 Mo) ; avertir si
   une image dépasse 300 Ko.
7. Tableau récapitulatif final par liste : résolues / manquantes / source
   (hades, position-map, tmdb, openlibrary, wiki-fr, wiki-en, recherche,
   conservée).

### 6. Livrables
`memo.html`, dossiers `thumbs/` et `full/`, `build/build_images.py`
(rejouable : ne retélécharge pas l'existant, permet de relancer après
corrections manuelles du CSV), `build/manifest.json`,
`build/rapport_manquants.csv`, et un court `build/README.md` (comment relancer
le build, comment corriger un manquant à la main : renseigner le titre ou
l'URL dans une colonne du CSV puis relancer).

## Critères d'acceptation (tous obligatoires)
- [ ] ≥ 98 % des cellules image ont un fichier local vérifié ; le reste est documenté.
- [ ] Mythologie = art Hades/Hades II par défaut ; départements = cartes de
      position rouge/bleu par défaut ; films = affiches TMDB.
- [ ] Ouverture de n'importe quelle liste : toutes les miniatures visibles
      immédiatement, app testée **hors ligne** sans aucune requête réseau.
- [ ] Le clic ouvre la version `full/` du même visuel.
- [ ] La migration v47 écrase les anciennes URLs cassées du localStorage mais
      préserve les uploads personnels.
- [ ] Boot test jsdom vert, rapport de couverture affiché.
