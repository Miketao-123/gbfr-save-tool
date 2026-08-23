import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
p = r'C:\Users\MikeT\Downloads\1.8.5\extracted\traits.json'
raw = open(p, 'rb').read()
if raw.startswith(b'\xef\xbb\xbf'): raw = raw[3:]
if not raw.lstrip().startswith(b'{'): raw = b'{' + raw
try:
    traits = json.loads(raw.decode('utf-8-sig'))
    open(p,'wb').write(raw)
except Exception as e:
    print('ERR', e); sys.exit()
arr = traits.get('traits', [])
print('traits count:', len(arr))
for e in arr:
    if e.get('internalId') == 'SKILL_324_00':
        print('SKILL_324_00 (天星之雪):')
        for k in ('displayName','category','maxLevel','canAppearAsPrimary','canAppearAsSecondary','bannedAsSecondaryOnPlusSigils','notes'):
            print(f'  {k}: {e.get(k)}')
gem = json.load(open('catalog_gem.json', encoding='utf-8'))
snow_h = 0xA898E283
for hk, e in gem['sigil_info'].items():
    if e.get('primary') == snow_h:
        sec = e.get('secondary')
        sec_txt = ('固定0x%08X' % sec) if (sec or 0x887AE0B0) != 0x887AE0B0 else '无/可自选'
        print()
        print('以天星之雪为主词条的因子:', e.get('cn') or e.get('name'), '0x%08X' % int(hk), '副词条:', sec_txt)
