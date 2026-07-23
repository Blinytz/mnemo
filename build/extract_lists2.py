import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

html = open(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\memo.html', encoding='utf-8').read()

def extract_rows(list_id):
    """Extrait les rows d'une liste depuis le JSON dans memo.html."""
    # Chercher {"id":"list_id",...,"rows":[[...],...]}
    pat = r'\{"id"\s*:\s*"' + re.escape(list_id) + r'".*?"rows"\s*:\s*(\[\[.*?\]\])'
    m = re.search(pat, html, re.DOTALL)
    if m:
        try:
            rows = json.loads(m.group(1))
            return rows
        except:
            pass
    # Essayer avec guillemets simples aussi
    pat2 = r"'id'\s*:\s*'" + re.escape(list_id) + r"'.*?'rows'\s*:\s*(\[\[.*?\]\])"
    m2 = re.search(pat2, html, re.DOTALL)
    if m2:
        try:
            return json.loads(m2.group(1))
        except:
            pass
    return None

for lst in ['montagnes_monde','mers_oceans','architectes_majeurs','xixe','philosophes']:
    rows = extract_rows(lst)
    if rows:
        print(f'\n{lst} ({len(rows)} rows):')
        for row in rows:
            num = row[0]
            # La colonne principale (nom) est généralement col 2
            name = row[2] if len(row) > 2 else '?'
            print(f'  {num}: {name}')
    else:
        print(f'\n{lst}: rows non trouvés')
