import json, io, sys, msgpack
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
st = json.load(open(r'system_table_skill_status.tbl.json', encoding='utf-8'))
skills = json.load(open(r'system_table_skill.tbl.json', encoding='utf-8'))
# get SKILL_301 rows from skill_status
h301 = 0xBF78FBFC
rows301 = sorted([r for r in st if r['Key']==h301], key=lambda r: r['Level'])
print('SKILL_301 skill_status rows:', len(rows301))
for r in rows301[:6]:
    print(f"  Level={r['Level']} LvDesc=0x{r['LevelDescription']:08X} vals={[r[f'LevelValue{i}'] for i in range(1,5)]}")
print('  ...')
print(f"  last: Level={rows301[-1]['Level']} LvDesc=0x{rows301[-1]['LevelDescription']:08X} vals={[rows301[-1][f'LevelValue{i}'] for i in range(1,5)]}")
# resolve LevelDescription hashes in text files
obj = msgpack.unpackb(open('_en_text.msg','rb').read(), raw=False)
rows = obj.get('rows_', [])
desc_hashes = set(r['LevelDescription'] for r in rows301)
for r in rows:
    col = r.get('column_', {})
    # the text key itself is what gets hashed; find entries whose id_hash hashes match
import sys as _s
_sys2 = __import__('sys')
_sys2.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from hashing import gbfr_hash
hits = []
for r in rows:
    col = r.get('column_', {})
    kid = col.get('id_hash_','')
    if kid and gbfr_hash(kid) in desc_hashes and col.get('subid_hash_','')=='':
        hits.append((kid, col.get('text_','')[:100]))
for kid, t in hits:
    print(f'LvDesc text {kid}: {t}')
