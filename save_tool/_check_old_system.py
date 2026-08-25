# -*- coding: utf-8 -*-
"""Check old-system summon hashes (3101-3115) against catalogs."""
import sys, os, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gbfr-save-editor', 'GBFR-Save-Editor-main', 'gbfr_editor', 'core'))
from gbfr_save import GBFRSaveData
from hashing import gbfr_hash

pet = r'C:\Users\MikeT\AppData\Local\Temp\pet'
summons = json.load(open(os.path.join(pet, 'data__summons.json'), encoding='utf-8'))['summons']
skills = json.load(open(os.path.join(pet, 'data__summon_skills.json'), encoding='utf-8'))['skills']
subs = json.load(open(os.path.join(pet, 'data__summon_sub_params.json'), encoding='utf-8'))['subParams']
summon_by_hash = {int(x['hash'], 16) & 0xFFFFFFFF: x for x in summons}
skill_by_hash = {int(x['hash'], 16) & 0xFFFFFFFF: x for x in skills}
sub_by_hash = {int(x['hash'], 16) & 0xFFFFFFFF: x for x in subs}

save_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames', 'SaveData1.dat')
s = GBFRSaveData.open(save_path)
u = 10109
for idt in (3101, 3102, 3105, 3106, 3107, 3109, 3110, 3111, 3112, 3113, 3114, 3115):
    recs = s.find(id_type=idt, unit_id=u)
    if not recs:
        continue
    vals = list(s.get_values(recs[0]))
    print(f'{idt}: {vals}')
    for v in vals:
        if isinstance(v, int) and (v & 0xFFFFFFFF) != 0x887AE0B0 and v != 0:
            h = v & 0xFFFFFFFF
            te = summon_by_hash.get(h)
            me = skill_by_hash.get(h)
            se = sub_by_hash.get(h)
            if te or me or se:
                print(f'   0x{h:08X} -> type={te["displayName"] if te else "-"} | main={me["displayName"] if me else "-"} | sub={se["displayName"] if se else "-"}')

# also try known summon string forms
print()
print('=== gbfr_hash probe for old-system 3113[0] ===')
tgt = 0xF1D4D831
for prefix in ('SUMMON', 'SO_', 'summon', 'SO', 'Summon'):
    for n in range(0, 5000):
        if gbfr_hash(f'{prefix}{n}') == tgt:
            print('FOUND:', f'{prefix}{n}')
# try the new catalog entries' hash sources
print()
print('=== check: do the new catalog displayName/code hash to the old values? ===')
for e in list(summon_by_hash.values())[:5]:
    for key in ('baseName', 'code', 'displayName'):
        s_ = e.get(key, '')
        h = gbfr_hash(s_)
        print(f'  gbfr_hash("{s_}") = 0x{h:08X}  (catalog entry hash 0x{e["hash"]})')
