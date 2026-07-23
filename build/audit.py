import sys, json, subprocess, pathlib
sys.stdout.reconfigure(encoding='utf-8')
REPO = pathlib.Path(__file__).parent.parent
result = subprocess.run(['node', str(REPO/'build'/'extract_data.js'), str(REPO/'memo.html')], capture_output=True, encoding='utf-8-sig')
data = json.loads(result.stdout)
THUMBS = REPO / 'thumbs'

print(f"{'Liste':<32} {'N':>5} {'Img':>5} {'Cols':>5}")
print('-' * 52)
for l in data['DEFAULT_LISTS']:
    lid = l['id']
    n = len(l['rows'])
    cols = len(l['columns']) - 2
    d = THUMBS / lid
    imgs = len(list(d.glob('*.webp'))) if d.exists() else 0
    sparse = ' << SPARSE' if n < 20 else ''
    noimg  = ' << IMG MISSING' if imgs < n else ''
    print(f"{lid:<32} {n:>5} {imgs:>5} {cols:>5}{sparse}{noimg}")
