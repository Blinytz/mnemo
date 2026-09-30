# Mémo, nouvelle version

Application issue de la refonte : révision espacée, quiz du jour, réponses
tapées. Elle vit dans `app/` tant que l'ancienne (`memo.html`) reste en place.
Adresse de test une fois publiée : https://blinytz.github.io/memo/app/

## Fichiers

| Fichier | Rôle |
|---|---|
| `index.html`, `style.css` | page et apparence (reprises de la maquette validée) |
| `js/main.js` | écrans, navigation, séances de révision et quiz du jour |
| `js/progression.js` | mémoire des fiches (boîtes de Leitner 1, 3, 7, 16, 35 jours), série, objectif du jour |
| `js/correction.js` | correction tolérante des réponses tapées |
| `js/questions.js` | fabrication des questions à partir d'une fiche |
| `js/eclats.js` | barème du quiz du jour et journal local des Éclats |
| `js/donnees.js` | lecture de `../data/catalogue.json` et `../data/listes/<id>.json` |
| `js/icones.js` | icônes Phosphor et glyphes de l'écosystème |
| `tests/` | tests sans écran : `node --test app/tests/` depuis la racine de Mémo |

## Données

Les listes viennent de `memo.html`, qui reste la source (l'Atelier et le
générateur WikiDeck y écrivent). Après toute modification :

```text
node build/exporter_donnees.mjs
```

## Stockage

Tout l'état tient sous la clé `memo2-etat` du stockage local (préfixe propre à
Mémo : le domaine blinytz.github.io est partagé par toutes les applis).

## Reste à faire

- Créditer les Éclats dans le registre commun (RPC `eclats_reward`, clé
  `memo-quiz-AAAA-MM-JJ`, déjà utilisée par le journal local).
- Hors ligne : service worker propre à la nouvelle version.
- Édition des listes et listes personnelles (encore dans l'ancienne version).
- Bascule : faire pointer `index.html` vers la nouvelle version.
