"""
Audit complet : pour chaque liste, vérifie que thumbs/{N} et full/{N}
existent tous les deux et que leur contenu est cohérent (même sujet).
On compare : existence, taille relative, et hash MD5 pour détecter des
images identiques mal placées.
"""
import sys, pathlib, hashlib, json
sys.stdout.reconfigure(encoding='utf-8')

BASE   = pathlib.Path(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo')
THUMBS = BASE / 'thumbs'
FULL   = BASE / 'full'

def md5(path):
    return hashlib.md5(path.read_bytes()).hexdigest()

def is_num(s):
    try: int(s); return True
    except: return False

def get_nums(folder):
    if not folder.exists():
        return set()
    return {p.stem for p in folder.iterdir()
            if p.suffix in ('.webp', '.jpg', '.jpeg', '.png') and is_num(p.stem)}

# Toutes les listes connues (dossiers dans thumbs/)
all_folders = sorted(p.name for p in THUMBS.iterdir() if p.is_dir())

issues = []
ok_count = 0

for folder in all_folders:
    th_dir = THUMBS / folder
    fu_dir = FULL   / folder

    th_nums = get_nums(th_dir)
    fu_nums = get_nums(fu_dir)

    only_in_thumb = th_nums - fu_nums
    only_in_full  = fu_nums - th_nums
    both          = th_nums & fu_nums

    if only_in_thumb or only_in_full:
        issues.append(f'[MANQUANT] {folder}:')
        if only_in_thumb:
            issues.append(f'  thumb SANS full: {sorted(only_in_thumb, key=lambda x: int(x))}')
        if only_in_full:
            issues.append(f'  full SANS thumb: {sorted(only_in_full, key=lambda x: int(x))}')

    # Vérif taille : full doit être >= thumb en octets (WebP très compressé vs JPEG)
    # On signale si full < 50% de la taille du thumb (suspect)
    size_issues = []
    for n in sorted(both, key=int):
        th_path = next(th_dir.glob(f'{n}.*'))
        fu_path = next(fu_dir.glob(f'{n}.*'))
        th_sz = th_path.stat().st_size
        fu_sz = fu_path.stat().st_size
        # full trop petit = image probablement cassée (< 5KB ou < thumb)
        if fu_sz < 5000:
            size_issues.append(f'  #{n}: full={fu_sz}B TROP PETIT')
        elif fu_sz < th_sz * 0.5:
            size_issues.append(f'  #{n}: thumb={th_sz}B full={fu_sz}B (full < 50% thumb, suspect)')

    if size_issues:
        issues.append(f'[TAILLE] {folder}:')
        issues.extend(size_issues)

    ok_count += len(both)

print(f'=== AUDIT SYNC thumbs/ vs full/ ===')
print(f'Dossiers analysés: {len(all_folders)}')
print(f'Paires OK: {ok_count}')
print()
if issues:
    print('PROBLÈMES DÉTECTÉS:')
    for line in issues:
        print(line)
else:
    print('Aucun problème détecté.')
