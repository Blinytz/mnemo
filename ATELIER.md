# Atelier Mémo

L’Atelier administre les catégories, listes, entrées, images et notes dans de
véritables fichiers locaux. Sa source de vérité est
`data/atelier/workspace.json`. Les anciennes données du navigateur ne sont plus
utilisées comme source éditoriale par l’Atelier.

## Premier lancement sur PC

```text
npm run atelier:migrate
npm run atelier
```

Ouvrir ensuite `http://127.0.0.1:3434/atelier/`.

La sauvegarde est automatique toutes les 30 secondes et disponible avec le
bouton **Enregistrer**. Chaque écriture crée d’abord une copie dans
`data/atelier/history/`, puis remplace le JSON atomiquement.

## Accès depuis un téléphone

Sur un réseau privé de confiance :

```text
$env:MEMO_HOST="0.0.0.0"
$env:MEMO_ATELIER_TOKEN="une-longue-valeur-secrete"
npm run atelier
```

Ouvrir `http://ADRESSE-IP-DU-PC:3434/atelier/`. Le service refuse les écritures
distantes sans le jeton envoyé par le client. Ne pas exposer ce port sur
Internet. Le PC doit rester allumé et le téléphone utilise exactement les mêmes
fichiers.

## Images et WikiDeck

Le format partagé est 800 × 600 pour la grande image et 213 × 160 pour la
miniature. La miniature est toujours dessinée depuis le même cadrage et la même
source que la grande image.

Exporter la collection Formule 1 :

```text
npm run atelier:export-f1
```

Dans l’Atelier, choisir **Importer WikiDeck** puis le `manifest.json` du paquet.
L’analyse est un dry-run : aucune donnée n’est modifiée avant confirmation.

## Restaurer une sauvegarde

Arrêter l’Atelier, copier le fichier voulu depuis `data/atelier/history/` vers
`data/atelier/workspace.json`, puis relancer. Conserver le fichier courant à
part avant de le remplacer.
