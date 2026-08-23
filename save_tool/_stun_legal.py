import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sig = json.load(open('catalog_sigils_full.json', encoding='utf-8'))
for e in sig['sigils']:
    if e.get('displayName') in ('Stun Power V+', '昏厥Ⅴ＋') or '昏厥' in (e.get('displayName') or ''):
        print(e.get('internalId'), e.get('displayName'), 'hash', e.get('hash'), 'allowedSecondaryTraitIds count:', len(e.get('allowedSecondaryTraitIds') or []))
        al = e.get('allowedSecondaryTraitIds') or []
        # check if 天星之雪 (SKILL with hash 0xA898E283) is there - need SKILL ids
        print('   allowed sample:', al[:8])
