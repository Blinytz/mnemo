import re, json, sys
sys.stdout.reconfigure(encoding='utf-8')
html = open(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\memo.html', encoding='utf-8').read()
pat = r'"id"\s*:\s*"xixe".*?"rows"\s*:\s*(\[\[.*?\]\])'
m = re.search(pat, html, re.DOTALL)
rows = json.loads(m.group(1))
for row in rows:
    print(f'{row[0]}\t{row[2]}\t{row[3]}\t{row[4] if len(row)>4 else ""}')
