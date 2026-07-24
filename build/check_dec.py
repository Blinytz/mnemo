import sys, json, re, pathlib
sys.stdout.reconfigure(encoding='utf-8')
html = open(r'C:\Users\flxjr\OneDrive\Documents\Ecosystème Eclats\apps\memo\memo.html', encoding='utf-8').read()
m = re.search(r'const CURATED_LISTS_V3 = (\[[\s\S]*?\]);\s*DEFAULT_LISTS\.push', html)
curated = json.loads(m.group(1))
dec = next(l for l in curated if l['id'] == 'decouvertes_scientifiques')
print(len(dec['rows']), 'entrees')
for r in dec['rows']:
    print(r[0], r[2])
