# -*- coding: utf-8 -*-
"""Full coverage check: all occupied summon records vs extracted 1.8.5 catalogs."""
import sys, os, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gbfr-save-editor', 'GBFR-Save-Editor-main', 'gbfr_editor', 'core'))
from gbfr_save import GBFRSaveData

summons = json.load(open('_patch_summon_summons.json', encoding='utf-8'))['summons']
skills = json.load(open('_patch_summon_skills.json', encoding='utf-8'))['skills']
subs = json.load(open('_patch_summon_subParams.json', encoding='utf-8'))['subParams']
summon_by_hash = {int(x['hash'], 16) & 0xFFFFFFFF: x for x in summons}
skill_by_hash = {int(x['hash'], 16) & 0xFFFFFFFF: x for x in skills}
sub_by_hash = {int(x['hash'], 16) & 0xFFFFFFFF: x for x in subs}

save_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames', 'SaveData1.dat')
s = GBFRSaveData.open(save_path)
m1456 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1456)}
m1457 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1457)}
m1458 = {r.unit_id: list(s.get_values(r)) for r in s.find(id_type=1458)}
m1459 = {r.unit_id: list(s.get_values(r)) for r in s.find(id_type=1459)}
m1460 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1460)}

occupied = 0
miss_type = miss_main = miss_sub = 0
empty_state = (0x887AE0B0, 0x887AE0B0, 0x887AE0B0, 0xFFFFFFFF, 0xFFFFFFFF, 0)
for u in sorted(m1457):
    slot = m1456.get(u, 0)
    th = m1457[u] & 0xFFFFFFFF
    mh, sh = m1458.get(u, [0, 0])
    ml, sl = m1459.get(u, [0, 0])
    rank = m1460.get(u, 0)
    state = (th, mh & 0xFFFFFFFF, sh & 0xFFFFFFFF, ml & 0xFFFFFFFF, sl & 0xFFFFFFFF, rank)
    if slot == 0 and state == empty_state:
        continue
    occupied += 1
    if th not in summon_by_hash:
        miss_type += 1
    if (mh & 0xFFFFFFFF) not in skill_by_hash:
        miss_main += 1
    if (sh & 0xFFFFFFFF) not in sub_by_hash:
        miss_sub += 1
print(f'occupied records: {occupied}')
print(f'missing: type={miss_type}, main_trait={miss_main}, sub_param={miss_sub}')

# equipped
print()
m1451 = s.find(id_type=1451)
for r in m1451:
    vals = list(s.get_values(r))
    print('1451 equipped slot ids:', vals)
    for v in vals:
        if v == 0:
            continue
        # find record with this slot
        for uu, sv in m1456.items():
            if sv == v:
                th = m1457[uu] & 0xFFFFFFFF
                print(f'  equipped slot {v} -> unit {uu}: {summon_by_hash.get(th, {}).get("displayName", "0x%08X" % th)}')
                break

# 1452 catalog missing
m1452 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1452)}
misscat = sum(1 for h in m1452.values() if (h & 0xFFFFFFFF) != 0x887AE0B0 and (h & 0xFFFFFFFF) not in summon_by_hash)
print(f'1452 catalog: {sum(1 for h in m1452.values() if (h & 0xFFFFFFFF) != 0x887AE0B0)} non-empty, {misscat} missing from catalog')
