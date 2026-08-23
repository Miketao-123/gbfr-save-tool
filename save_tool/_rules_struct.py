import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
rules = json.load(open(r'C:\Users\MikeT\Downloads\1.8.5\extracted\secondary-trait-rules.json', encoding='utf-8-sig'))
print('top keys:', list(rules.keys()))
r = rules.get('rules', rules)
if isinstance(r, list):
    print('rules count:', len(r))
    print('sample:', json.dumps(r[0], ensure_ascii=False)[:500])
elif isinstance(r, dict):
    ks = list(r.keys())[:5]
    print('rules dict keys:', ks)
    print('sample:', json.dumps(r[ks[0]], ensure_ascii=False)[:500])
