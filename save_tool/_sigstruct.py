import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sig = json.load(open(r'C:\Users\MikeT\Downloads\1.8.5\extracted\sigils.json', encoding='utf-8-sig'))
arr = sig['sigils']
print('sigils:', len(arr))
s = arr[0]
print('entry keys:', list(s.keys()))
# count entries with allowedSecondaryTraitIds non-empty
with_sec = [x for x in arr if x.get('allowedSecondaryTraitIds')]
print('entries with allowed secondary list:', len(with_sec))
# sample a few entries
for name in ['Crabby Resonance', 'Crabmiration', 'Glass Cannon V+']:
    hit = [x for x in arr if x.get('displayName') == name]
    if hit:
        e = hit[0]
        print(name, '->', e.get('internalId'), 'supportsSecondary:', e.get('supportsSecondaryTrait'), 'allowed:', (e.get('allowedSecondaryTraitIds') or [])[:6])
