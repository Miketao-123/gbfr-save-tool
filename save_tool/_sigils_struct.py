import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sig = json.load(open(r'C:\Users\MikeT\Downloads\1.8.5\extracted\sigils.json', encoding='utf-8-sig'))
print('top keys:', list(sig.keys()))
arr = sig.get('sigils', [])
print('sigils count:', len(arr))
if arr:
    s0 = arr[0]
    print('entry keys:', list(s0.keys()))
    print('sample:', json.dumps({k: s0[k] for k in list(s0.keys())[:12]}, ensure_ascii=False)[:500])
