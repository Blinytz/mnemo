import sys, json, subprocess, pathlib
sys.stdout.reconfigure(encoding='utf-8')
REPO = pathlib.Path(__file__).parent.parent
result = subprocess.run(['node', str(REPO/'build'/'extract_data.js'), str(REPO/'memo.html')], capture_output=True, encoding='utf-8-sig')
data = json.loads(result.stdout)
lid = sys.argv[1]
l = next(x for x in data['DEFAULT_LISTS'] if x['id'] == lid)
print('Colonnes:', l['columns'])
print(f'{len(l["rows"])} entrées:')
for r in l['rows']:
    print(' ', r)
