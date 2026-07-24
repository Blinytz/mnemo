import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

html = open(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\memo.html', encoding='utf-8').read()

# Trouver le bloc APP_DATA ou les listes directement
targets = ['montagnes_monde','mers_oceans','philosophes','xixe','architectes_majeurs','musiques','religions']

# Chercher les définitions de listes dans le JS
# Format typique: {id:'montagnes_monde', items:[...]}
for lst in targets:
    pat = r'\{[^{}]*id\s*:\s*[\'"]' + lst + r'[\'"][^{}]*items\s*:\s*(\[[^\]]*(?:\[[^\]]*\][^\]]*)*\])'
    m = re.search(pat, html, re.DOTALL)
    if m:
        try:
            items = json.loads(m.group(1))
            print(f'\n{lst} ({len(items)} items):')
            for i, item in enumerate(items, 1):
                name = item if isinstance(item, str) else item.get('name', item.get('r2', str(item)))
                print(f'  {i}: {repr(name)}')
        except Exception as e:
            print(f'{lst}: erreur parsing - {e}')
            print(m.group(1)[:200])
    else:
        # Cherche juste l'id
        idx = html.find(f"'{lst}'")
        if idx < 0: idx = html.find(f'"{lst}"')
        if idx >= 0:
            print(f'\n{lst} trouvé à {idx}:')
            print(html[idx-20:idx+300])
        else:
            print(f'\n{lst}: NON TROUVÉ')
