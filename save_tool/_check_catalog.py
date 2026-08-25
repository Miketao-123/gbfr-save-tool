# -*- coding: utf-8 -*-
"""Cross-check save summon hashes against PE Patch Tool catalogs."""
import sys, os, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gbfr-save-editor', 'GBFR-Save-Editor-main', 'gbfr_editor', 'core'))
from gbfr_save import GBFRSaveData

pet = r'C:\Users\MikeT\AppData\Local\Temp\pet'
summons = json.load(open(os.path.join(pet, 'data__summons.json'), encoding='utf-8'))['summons']
skills = json.load(open(os.path.join(pet, 'data__summon_skills.json'), encoding='utf-8'))['skills']
subs = json.load(open(os.path.join(pet, 'data__summon_sub_params.json'), encoding='utf-8'))['subParams']

summon_by_hash = {int(x['hash'], 16) & 0xFFFFFFFF: x for x in summons}
skill_by_hash = {int(x['hash'], 16) & 0xFFFFFFFF: x for x in skills}
sub_by_hash = {int(x['hash'], 16) & 0xFFFFFFFF: x for x in subs}
print(f'catalogs: {len(summon_by_hash)} types, {len(skill_by_hash)} main traits, {len(sub_by_hash)} sub params')

save_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames', 'SaveData1.dat')
s = GBFRSaveData.open(save_path)

# 1) catalog 1452
print()
print('=== 1452 catalog hashes coverage ===')
m1452 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1452)}
miss = 0
for u, h in sorted(m1452.items()):
    h &= 0xFFFFFFFF
    e = summon_by_hash.get(h)
    if not e:
        miss += 1
        if miss <= 10:
            print(f'  MISS unit={u} 0x{h:08X}')
print(f'  1452: {len(m1452)} entries, {miss} missing from catalog')

# 2) types 1457 + traits 1458 + levels 1459 + rank 1460 for first 12 records
print()
print('=== first 12 inventory records (1456-1460) ===')
m1456 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1456)}
m1457 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1457)}
m1458 = {r.unit_id: list(s.get_values(r)) for r in s.find(id_type=1458)}
m1459 = {r.unit_id: list(s.get_values(r)) for r in s.find(id_type=1459)}
m1460 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1460)}
shown = 0
for u in sorted(m1457):
    slot = m1456.get(u, 0)
    if slot == 0:
        continue
    th = m1457[u] & 0xFFFFFFFF
    mh, sh = m1458.get(u, [0, 0])
    ml, sl = m1459.get(u, [0, 0])
    rank = m1460.get(u, 0)
    te = summon_by_hash.get(th)
    me = skill_by_hash.get(mh & 0xFFFFFFFF)
    se = sub_by_hash.get(sh & 0xFFFFFFFF)
    print(f'  slot={slot:>4} unit={u:<4} type={te["displayName"] if te else "0x%08X" % th:<24} '
          f'main={me["displayName"] if me else "0x%08X" % mh:<18} lv{ml:<3} '
          f'sub={se["displayName"] if se else "0x%08X" % sh:<16} lv{sl:<3} rank={rank}')
    shown += 1
    if shown >= 12:
        break
