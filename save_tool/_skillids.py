import re, json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
base = r'C:\Users\MikeT\Downloads\1.8.5\extracted'
for fn in ['traits.json','wrightstone_traits.json']:
    txt = open(f'{base}\{fn}', encoding='utf-8').read()
    ids = re.findall(r'"internalId"\s*:\s*"SKILL_([0-9A-Fa-f]+)_(\d+)"', txt)
    nums = sorted(set(int(a,16) for a,b in ids))
    print(f'=== {fn}: {len(ids)} entries, {len(nums)} unique SKILL ids ===')
    print('  min:', min(nums), 'max:', max(nums))
    print('  ids:', nums)
