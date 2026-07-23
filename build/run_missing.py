#!/usr/bin/env python3
"""Lance build_images.py séquentiellement pour les listes avec couverture < 100%."""
import subprocess, sys, pathlib, json

BUILD = pathlib.Path(__file__).parent
REPO  = BUILD.parent
THUMBS = REPO / 'thumbs'

TARGETS = {
    'civilisations': 28,
    'fleuves_monde': 30,
    'compositeurs': 39,
    'constellations': 38,
    'grands_scientifiques': 38,
    'batailles_decisives': 33,
    'grandes_explorations': 25,
    'montagnes_monde': 30,
    'detroits_monde': 20,
    'parcs_nationaux': 30,
    'architectes_majeurs': 30,
    'musees_monde': 25,
}

for lst, target in TARGETS.items():
    d = THUMBS / lst
    current = len(list(d.glob('*.webp'))) if d.exists() else 0
    if current >= target:
        print(f'  ✓ {lst}: {current}/{target} — OK')
        continue
    print(f'  ▶ {lst}: {current}/{target} — lancement...')
    r = subprocess.run(
        [sys.executable, str(BUILD / 'build_images.py'), '--list', lst, '--no-patch'],
        cwd=BUILD
    )
    after = len(list(d.glob('*.webp'))) if d.exists() else 0
    print(f'    → {after}/{target} après build')
