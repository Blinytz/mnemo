# Atelier Mnémo

L'Atelier sert à mettre à jour les images de Mnémo. Ce qu'on y enregistre est
écrit **dans l'application** : les fichiers image et `memo.html` sont mis à jour
d'un seul geste, et la miniature est toujours découpée dans le même cadrage que
la grande image. Il n'y a donc jamais deux choses à gérer séparément.

## Ouvrir

Deux accès existent, et ils ne se remplacent pas l'un l'autre.

**En ligne, sans rien lancer** : <https://blinytz.github.io/mnemo/atelier.html>.
C'est le lien à garder en favori. Il écrit dans `Blinytz/mnemo` et demande
donc un jeton GitHub (bouton ⚙). Ses sources sont dans `atelier-en-ligne/`.
L'ancienne adresse `memo-web` ne fait plus que rediriger ici (depuis le 29/09/2026).

**En local** — écrit directement dans les fichiers de ce dossier :

```text
npm run atelier
```

Puis ouvrir `http://127.0.0.1:3434/atelier/`. Cette adresse ne répond que tant
que la commande tourne : si le lien « ne marche pas », c'est en général que le
service est arrêté.

Attention : l'« Atelier des Cartes » de WikiDeck
(`blinytz.github.io/wikideck/atelier.html`) est un autre outil, il n'ouvre pas
les listes de Mnémo. En revanche les deux ateliers partagent désormais la même
interface — mêmes onglets, même grille, même éditeur — pour qu'on passe de l'un
à l'autre sans réapprendre.

La version en ligne a quatre écrans : **Grille** (toutes les listes d'un coup
avec un sommaire), **Tableau**, **Notes** et **⚙** (connexion GitHub et état).
La reprise WikiDeck n'existe que dans la version locale.

Au premier lancement seulement, si `data/atelier/workspace.json` n'existe pas :

```text
npm run atelier:migrate
```

Les données éditoriales de l'Atelier vivent dans `data/atelier/workspace.json`.
Elles sont enregistrées automatiquement toutes les 30 secondes et avec le bouton
**Enregistrer** ; chaque écriture dépose d'abord une copie dans
`data/atelier/history/`.

## Les cinq écrans

- **Grille** — toutes les entrées en vignettes. C'est l'écran de tri : l'image
  qui ne va pas saute aux yeux. Filtres par liste, par statut, par « sans
  image », et recherche par nom. La pastille en haut à gauche d'une vignette
  bascule entre « à vérifier » et « validée » d'un clic.
- **Tableau** — la même liste sous forme de tableur, pour le travail sur les
  données (numéros, noms, colonnes).
- **Reprise WikiDeck** — récupère le travail d'images déjà fait dans WikiDeck.
- **Notes** — remarques à traiter plus tard.
- **⚙ Entretien** — état de l'installation et correction des noms d'entrées.

## Recadrer une image

Un clic sur une vignette ouvre l'éditeur. On glisse la photo sous le cadre, on
zoome à la molette ou au pincement ; le cadre est exactement ce que Mnémo
affichera, et la miniature à droite se redessine en direct.

Le zoom minimum couvre toujours le cadre : il est **impossible** de produire une
image avec des bandes vides. Si une image ancienne comporte des bandes noires,
c'est qu'elles sont dans le fichier d'origine — il suffit de zoomer pour les
sortir du cadre.

Pour changer d'image : bouton **Remplacer**, coller une URL, coller l'image
elle-même avec Ctrl+V, ou la déposer dans la fenêtre.

**Enregistrer l'image** écrit d'un coup :

| fichier | format | rôle |
| --- | --- | --- |
| `originaux/<liste>/<clé>.webp` | ≤ 2400 px | la source, pour recadrer plus tard sans perte |
| `full/<liste>/<clé>.webp` | 2000 × 1500 | la grande image de Mnémo |
| `thumbs/<liste>/<clé>.webp` | 400 × 300 | la miniature de Mnémo |

…et met à jour `memo.html` dans la foulée. Une copie du fichier est déposée dans
`backups/` avant la première écriture de la journée.

## Reprendre le travail fait dans WikiDeck

L'atelier WikiDeck a déjà cadré des centaines d'images. Plutôt que de chercher
les mêmes photos une seconde fois, on apparie une liste de Mnémo à une collection
WikiDeck.

L'appariement ne peut pas se faire sur le lien Wikipédia : les entrées de Mnémo
n'en avaient aucun. Il se fait sur **la colonne qui porte le sujet** — pour la
Formule 1 c'est « Pilote », pas « Année ». `memo.html` déclare lui-même cette
colonne pour chaque liste, l'Atelier la propose donc d'office ; l'écran affiche
le nombre de correspondances par colonne si l'on veut en essayer une autre.

Le lien Wikipédia voyage dans l'autre sens : c'est WikiDeck qui en fournit un à
Mnémo au passage.

Marche à suivre : choisir la liste et la collection, vérifier le tableau des
paires, décocher ce qu'on ne veut pas, puis importer. Rien n'est écrit avant
confirmation. Les entrées verrouillées ne sont jamais remplacées, et une entrée
sur laquelle plusieurs cartes portent le même nom est signalée « ambiguë » et
laissée de côté.

Plusieurs entrées peuvent viser la même carte : les 76 saisons de Formule 1 se
partagent 35 pilotes, c'est normal.

## Corriger les noms d'entrées

La migration d'origine avait retenu la mauvaise colonne comme nom sur neuf
listes — les champions de Formule 1 s'appelaient « 1950 », « 1951 »… L'écran
**Entretien** propose la correction, colonne par colonne, avec l'aperçu
avant/après. Ces noms ne servent qu'à l'Atelier : l'application n'est pas
touchée.

## Accès depuis un téléphone

Sur un réseau privé de confiance :

```text
$env:MEMO_HOST="0.0.0.0"
$env:MEMO_ATELIER_TOKEN="une-longue-valeur-secrete"
npm run atelier
```

Ouvrir `http://ADRESSE-IP-DU-PC:3434/atelier/`. Le service refuse les écritures
distantes sans le jeton. Ne pas exposer ce port sur Internet. Le PC doit rester
allumé et le téléphone utilise exactement les mêmes fichiers.

## Comment l'Atelier écrit dans `memo.html`

`memo.html` construit ses listes par trois chemins qui se cumulent :
`DEFAULT_LISTS` et `CURATED_LISTS_V3` sont du JSON, `EXPANSION_LISTS` est du
JavaScript écrit à la main. Réécrire ce dernier serait risqué.

L'Atelier ne touche donc pas aux listes elles-mêmes. Il tient un bloc à part,
`ATELIER_IMAGES`, inséré après le dernier apport à `DEFAULT_LISTS` et appliqué
au chargement de l'application. Un seul endroit à écrire, valable pour les trois
provenances, et le travail de l'Atelier reste lisible d'un coup d'œil. Les
grandes images passent par `IMAGE_FILES_MAP`, qui est déjà du JSON.

## Restaurer

- L'application : copier le fichier voulu de `backups/memo-AAAA-MM-JJ.html` vers
  `memo.html`.
- Les données de l'Atelier : arrêter le service, copier le fichier voulu de
  `data/atelier/history/` vers `data/atelier/workspace.json`, relancer.

`thumbs/`, `memo.html`, et les fichiers de `full/` et `originaux/` utilisés par
l'application sont versionnés et publiés. Les deux derniers dossiers restent
ignorés par Git : un nouveau fichier s'y ajoute avec `git add -f`, pour ne pas
embarquer les brouillons locaux.
