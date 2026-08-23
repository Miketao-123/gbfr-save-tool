import json, io, sys, msgpack
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from hashing import gbfr_hash
gems = json.load(open(r'system_table_gem.tbl.json', encoding='utf-8'))
skills = json.load(open(r'system_table_skill.tbl.json', encoding='utf-8'))
for gid in ['GEEN_301_00','GEEN_301_10','GEEN_302_00','GEEN_303_00']:
    h = gbfr_hash(gid)
    rows = [g for g in gems if g['Key'] == h]
    print(f'=== {gid} hash=0x{h:08X} ===')
    for g in rows:
        print(f"  SkillId1=0x{g['SkillId1']:08X} SkillId2=0x{g['SkillId2']:08X} Rarity={g['Rarity']} Category={g['Category']} Hold1={g['CanOnlyHoldOne']} HideLv={g['HideLevelNumber']} Mix={g['CanGemMix']}")
# skill rows for 301/302/303
for snum in [301, 302, 303]:
    h = gbfr_hash(f'SKILL_{snum}_00')
    rows = [r for r in skills if r['Key'] == h]
    if rows:
        r = rows[0]
        print(f"SKILL_{snum}_00: GemCat={r['GemCategory']} QuestId=0x{r['QuestId']:X} Unk11={r['Unk11']} Unk12={r['Unk12']} IsRes={r['IsResistance']}")
# skill summaries from cs text
obj = msgpack.unpackb(open('_cs_text.msg','rb').read(), raw=False)
for r in obj.get('rows_', []):
    col = r.get('column_', {})
    kid = col.get('id_hash_','')
    if kid in ('TXT_SKILL_SUMMARY_301_00','TXT_SKILL_SUMMARY_302_00','TXT_SKILL_EXPLAIN_301_00'):
        print(f'{kid}: {col.get("text_","")}')
