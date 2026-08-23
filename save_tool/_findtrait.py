import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from hashing import gbfr_hash
skills = json.load(open(r'system_table_skill.tbl.json', encoding='utf-8'))
gems = json.load(open(r'system_table_gem.tbl.json', encoding='utf-8'))
st = json.load(open(r'system_table_skill_status.tbl.json', encoding='utf-8'))

# search skill table by name hash
for name in ['Dread Black Pincer Crab Sigil', '可怕的漆黑钳蟹因子', 'Crabby Resonance', '钳蟹的共鸣']:
    h = gbfr_hash(name)
    hits = [r for r in skills if r['Name'] == h]
    print(f'name={name!r} hash=0x{h:08X} -> {len(hits)} skill rows')
    for r in hits[:3]:
        print('   ', {k: (f'0x{v:08X}' if isinstance(v,int) else v) for k,v in r.items()})
print()
# list all skills with GemCategory != 0 or interesting (highest Key hex)
print('=== all skill rows (Key, Name hash, GemCategory, QuestId) ===')
for r in skills:
    print(f"  Key=0x{r['Key']:08X} Name=0x{r['Name']:08X} GemCat={r['GemCategory']} QuestId=0x{r['QuestId']:08X}")
