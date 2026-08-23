import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
skills = json.load(open(r'system_table_skill.tbl.json', encoding='utf-8'))
gems = json.load(open(r'system_table_gem.tbl.json', encoding='utf-8'))
# sort skills by SortOrderMaybe numeric
def skey(r):
    try: return int(r['SortOrderMaybe'])
    except: return 0
skills_sorted = sorted(skills, key=skey)
print('=== highest SKILL rows (SortOrderMaybe) ===')
for r in skills_sorted[-40:]:
    print(f"  #{r['SortOrderMaybe']:<5} Key=0x{r['Key']:08X} GemCat={r['GemCategory']} Unk1=0x{r['Unk1']:08X} Icon={r['IconId1']!r}")
# find gems whose Key matches Unk1 of these high skills -> the reward gems
print()
print('=== gems for the high skills (by Unk1) ===')
high = {r['Unk1'] for r in skills_sorted[-40:] if r['Unk1'] != 0x887AE0B0}
for g in gems:
    if g['Key'] in high:
        print(f"  gem Key=0x{g['Key']:08X} Skill1=0x{g['SkillId1']:08X} Skill2=0x{g['SkillId2']:08X} Rarity={g['Rarity']} Category={g['Category']} Hold1={g['CanOnlyHoldOne']} HideLv={g['HideLevelNumber']} CantSell={g['CantSell']}")
