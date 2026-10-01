# Atelier Mnémo en ligne

Version navigateur de l'Atelier, publiée à l'adresse
<https://blinytz.github.io/mnemo/atelier.html>.

Il écrit directement dans le dépôt `Blinytz/mnemo` (branche `main`) par l'API
GitHub, avec un jeton gardé en `sessionStorage`. Chaque enregistrement est un
commit, qui relance la publication GitHub Pages.

À la publication (`.github/workflows/deploy-pages.yml`), ce dossier est rangé
ainsi : `atelier.html` à la racine du site, les autres fichiers dans `atelier/`.
Les adresses restent donc celles de l'ancienne copie `memo-web`.

Ne pas confondre avec `atelier/` à la racine du dépôt : c'est l'Atelier local
(`npm run atelier`), qui écrit sur le disque.
