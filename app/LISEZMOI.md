# Mémo, nouvelle version

Application issue de la refonte : révision espacée, quiz du jour, réponses
tapées. C'est la version officielle depuis le 01/10/2026 ; l'ancienne reste
accessible avec `memo.html?ancienne`.
En ligne : https://blinytz.github.io/memo/app/

## Fichiers

| Fichier | Rôle |
|---|---|
| `index.html`, `style.css` | page et apparence (reprises de la maquette validée) |
| `js/main.js` | écrans, navigation, séances de révision et quiz du jour, réglages |
| `js/ui.js` | petits outils d'affichage partagés |
| `js/edition.js` | modifications des listes sur l'appareil (couche par-dessus les listes officielles), listes personnelles, tableaux collés, reprise de l'ancienne version |
| `js/ecrans-edition.js` | formulaires : fiche, nouvelle liste, liste personnelle |
| `js/images-perso.js` | photos importées, rangées dans IndexedDB |
| `js/registre.js` | client du registre commun (copie de celui de Sport, app_id `memo`) |
| `js/progression.js` | mémoire des fiches (boîtes de Leitner 1, 3, 7, 16, 35 jours), série, objectif du jour |
| `js/correction.js` | correction tolérante des réponses tapées |
| `js/questions.js` | fabrication des questions à partir d'une fiche |
| `js/eclats.js` | barème du quiz du jour, journal des gains, versement dans le registre |
| `js/donnees.js` | lecture de `../data/catalogue.json` et `../data/listes/<id>.json` |
| `js/icones.js` | icônes Phosphor et glyphes de l'écosystème |
| `tests/` | tests sans écran : `node --test "app/tests/*.test.mjs"` depuis la racine de Mémo |

## Données

Les listes viennent de `memo.html`, qui reste la source (l'Atelier et le
générateur WikiDeck y écrivent). Après toute modification :

```text
node build/exporter_donnees.mjs
```

## Règles de fonctionnement

- **Quiz du jour** : 20 questions, une par liste. Les listes jamais posées ou
  posées il y a le plus longtemps passent en premier (79 listes : tour complet
  en 4 jours) ; dans une liste, la fiche la moins récemment posée. Le barème est
  réglable (Réglages, roue dentée) et figé au lancement de chaque quiz.
- **À découvrir** (accueil) : 8 listes pas encore suivies. Les listes apparues
  depuis moins de 14 jours passent devant avec un badge « Nouvelle » ; les autres
  changent d'ordre chaque jour.
- **Liens** : l'article Wikipédia exact quand la fiche vient de WikiDeck
  (`wiki` dans les données), sinon une recherche Wikipédia (Wiktionnaire pour
  les listes de vocabulaire).
- **Listes ajoutées ou retirées** : le catalogue donne les identifiants de toutes
  les fiches (`ids`). Une fiche absente du catalogue garde sa progression mais
  sort de tous les calculs (fiches dues, mémoire, maîtrise) ; elle revient avec
  sa liste. L'identifiant d'une fiche est la clé de son image : corriger un nom
  ne fait pas perdre la progression. Une question du quiz dont la liste a
  disparu est remplacée.

## Stockage

Tout l'état tient sous la clé `memo2-etat` du stockage local (préfixe propre à
Mémo : le domaine blinytz.github.io est partagé par toutes les applis).

## Hors ligne et mises à jour

- `../sw.js` garde l'application, le catalogue et les 79 listes dès
  l'installation, puis chaque image affichée ; une séance charge d'avance toutes
  ses grandes images.
- `version.json`, écrit au déploiement, est relu au retour au premier plan :
  l'application se recharge seule si rien n'est en cours, sinon un bandeau
  propose d'actualiser.

## Registre commun

Les gains du quiz restent « à verser » jusqu'à ce que l'utilisateur les verse
(Réglages, ou fin du quiz). La session `eclats_session` est partagée avec les
autres applis du domaine. Rien n'est jamais dépensé depuis Mémo.

## Données de l'utilisateur

`memo2-etat` (progression, quiz, gains, réglages) et `memo2-listes`
(modifications et listes personnelles) dans le stockage local ; photos dans
IndexedDB (`memo2-images`). Réglages > Mes données : sauvegarde et restauration
en un fichier JSON, reprise des listes personnelles de l'ancienne version.
