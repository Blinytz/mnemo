#!/usr/bin/env python3
"""Télécharge les images manquantes pour les 4 listes nouvellement enrichies."""
import sys, subprocess, pathlib, json
sys.stdout.reconfigure(encoding='utf-8')

REPO = pathlib.Path(__file__).parent.parent
BUILD = REPO / 'build'
THUMBS = REPO / 'thumbs'

TARGETS = {
    'revolutions': 30,
    'mers_oceans': 20,
    'inventions_majeures': 35,
    'decouvertes_scientifiques': 30,
}

for lid, expected in TARGETS.items():
    existing = len(list((THUMBS / lid).glob('*.webp'))) if (THUMBS / lid).exists() else 0
    if existing >= expected:
        print(f'[SKIP] {lid}: {existing}/{expected} images OK')
        continue
    print(f'[BUILD] {lid}: {existing}/{expected} images, téléchargement...')
    r = subprocess.run(
        [sys.executable, str(BUILD / 'build_images.py'), '--list', lid],
        cwd=str(REPO),
        capture_output=False,
        text=True,
        encoding='utf-8',
    )
    after = len(list((THUMBS / lid).glob('*.webp'))) if (THUMBS / lid).exists() else 0
    print(f'  -> {after} images')
    if r.returncode != 0:
        print(f'  ERREUR build {lid}')

print('\nTerminé.')
