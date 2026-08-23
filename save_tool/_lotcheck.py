import json, io, sys, urllib.request
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
gems = json.load(open('system_table_gem.tbl.json', encoding='utf-8'))
for g in gems:
    if g['Key'] == 0x791DA8ED:  # 昏厥Ⅴ＋ 新版
        print('GEEN_004_24 (昏厥Ⅴ＋ 新版):')
        print('  SkillTypeLotIdForRandom2ndSkill:', g['SkillTypeLotIdForRandom2ndSkill'])
        print('  SkillId1:', hex(g['SkillId1']), ' SkillId2:', hex(g['SkillId2']))
# fetch skill_lot headers
h = urllib.request.urlopen(urllib.request.Request('https://raw.githubusercontent.com/Nenkai/GBFRDataTools/master/GBFRDataTools.Database/Headers/skill_lot.headers', headers={'User-Agent':'Mozilla/5.0'}), timeout=30).read().decode('utf-8','replace')
print()
print('=== skill_lot.headers ===')
print(h[:1500])
