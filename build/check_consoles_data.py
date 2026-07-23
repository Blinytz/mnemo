"""Trouver le bon numéro de la PlayStation dans les données."""
import sys, json, re
sys.stdout.reconfigure(encoding='utf-8')

# Lire les données depuis memo.html
with open(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\memo.html', encoding='utf-8') as f:
    content = f.read()

# Chercher la liste consoles
m = re.search(r"id:\s*'consoles[_a-z]*'.*?rows:\s*\[([^\]]{0,5000})\]", content, re.DOTALL)
if m:
    rows_txt = '[' + m.group(1) + ']'
    try:
        rows = json.loads(rows_txt)
        for i, row in enumerate(rows, 1):
            print(f'#{i:3d}: {row}')
    except Exception as e:
        # Chercher autrement
        lines = [l.strip() for l in m.group(1).split('\n') if 'PlayStation' in l or 'playstation' in l.lower()]
        for l in lines:
            print(l)
else:
    # Chercher toutes les lignes PlayStation dans les données
    matches = re.findall(r'\["([^"]*)",.*?"([^"]*PlayStation[^"]*)".*?\]', content)
    for m2 in matches[:10]:
        print(m2)
