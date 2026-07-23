import sys, re, pathlib
sys.stdout.reconfigure(encoding='utf-8')
html = open(r'C:\Users\flxjr\OneDrive\Bureau\memo-app\memo.html', encoding='utf-8').read()

m = re.search(r'const DEFAULT_LISTS = (\[)', html)
start = m.start(1)
depth = 0
i = start
while i < len(html):
    if html[i] == '[': depth += 1
    elif html[i] == ']':
        depth -= 1
        if depth == 0: break
    i += 1
base_section = html[start:i+1]
ids = re.findall(r'"id"\s*:\s*"([^"]+)"', base_section)
print('Base DEFAULT_LISTS:', len(ids), 'listes')
print('IDs:', ids)
