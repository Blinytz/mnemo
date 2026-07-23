# Audit visuel v60

Date: 2026-06-19

## Methode

- 64 planches de contact generees depuis les assets locaux.
- Controle manuel des images de chaque liste et de chaque colonne image.
- Controle structurel de tous les chemins dans `memo.html`.
- Test Chromium local avec les requetes externes absentes.
- Les originaux de chaque remplacement sont conserves dans
  `build/asset_backups/v60`.

## Etat valide

- 23 listes et toutes les cellules image ont un chemin local valide.
- 0 chemin local manquant dans `memo.html`.
- L'application v60 affiche les 23 cartes de liste dans Chromium local.
- Mythologie: 59 miniatures sur 59 chargees sans erreur.
- Os: les images manifestement hors sujet ont ete remplacees par des schemas
  anatomiques coherents et cibles.
- Peintres: les oeuvres de Michel-Ange, Rubens, Cezanne, Picasso, Rivera,
  De Chirico, Kahlo, Bacon, Basquiat et Banksy ont ete corrigees.
- Rois de France: les genealogies generiques de Clotaire II, Clotaire III,
  Childebert III, Carloman II, Robert Ier, Raoul et Lothaire ont ete
  remplacees.
- Periodes geologiques: Tonien et Trias ne sont plus des fiches neutres.
- XIXe et XXe: 1859, 1895, 1902 et 1943 ne sont plus des fiches neutres.
- Chefs d'Etat: Mac-Mahon est corrige; le Directoire est represente par un
  personnage de son regime.
- Lunes: Leda et Pasiphae ont maintenant des observations astronomiques.

## Encore a resoudre avant de declarer 100 pourcent visuel

Ces lignes gardent leur ancien asset, sauvegarde, tant qu'une source plus
specifique n'est pas telechargee:

| Liste | Ligne | Motif |
| --- | --- | --- |
| Films | 15, 23, 27, 51 | Cartes de titre ou logos Pathé; TMDB et Commons ne fournissent pas de visuel fiable pour ces films muets. |
| Lunes | 22, 23, 28, 42, 44 | Promethee, Pandore, Calypso, Caliban et Naiade affichent encore un visuel mythologique ou generique. |
| Peintres | 43b | La colonne oeuvre de Pollock affiche encore un portrait; Commons a identifie une oeuvre mais le CDN etait limite lors du telechargement. |
| Litterature | 56 | Le Guide du voyageur galactique a encore un portrait d'auteur, car les API de couverture n'ont renvoye aucune couverture exploitable. |
| Chefs d'Etat | 3 | La Convention est representee par le schema de ses 786 deputes; pedagogiquement pertinent mais visuellement different des portraits du reste de la liste. |

## Fichiers produits

- `build/fix_visual_quality_v60.py`: remplacements sources et journalises.
- `build/fix_os_anatomy_schematics.py`: schemas locaux anatomiques.
- `build/quality_replacements_v60_*.json`: resultat par lot.
- `build/audit_sheets/`: 64 planches de controle.
- `build/asset_backups/v60/`: 237 fichiers precedents conserves.
