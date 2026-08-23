import json, io, sys, msgpack
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from hashing import gbfr_hash
# find SKILL id of 天星之雪 (trait hash 0xA898E283)
obj = msgpack.unpackb(open('_cs_text.msg','rb').read(), raw=False)
for r in obj.get('rows_', []):
    col = r.get('column_', {})
    if col.get('text_','') == '天星之雪' and col.get('subid_hash_','') == '':
        kid = col.get('id_hash_','')
        gid = kid[len('TXT_'):]
        print('天星之雪 ->', gid, 'hash=0x%08X' % gbfr_hash(gid))
# check allowed list of GEEN_004_24
sig = json.load(open('catalog_sigils_full.json', encoding='utf-8'))
for e in sig['sigils']:
    if e.get('internalId') == 'GEEN_004_24':
        al = e.get('allowedSecondaryTraitIds') or []
        print('GEEN_004_24 允许副词条数:', len(al))
        # check if 天星之雪 SKILL id is in it
        snow_id = None
        for r in obj.get('rows_', []):
            col = r.get('column_', {})
            if col.get('text_','') == '天星之雪' and col.get('subid_hash_','') == '':
                snow_id = col.get('id_hash_','')[len('TXT_'):]
        print('天星之雪 SKILL id:', snow_id, '在合法池:', snow_id in al)
        # also check 昏厥 主词条 SKILL id
        break
