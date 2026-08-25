# -*- coding: utf-8 -*-
"""Verify empty-record state matches PE Patch Tool expectations; check API."""
import sys, os, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gbfr-save-editor', 'GBFR-Save-Editor-main', 'gbfr_editor', 'core'))
from gbfr_save import GBFRSaveData

save_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames', 'SaveData1.dat')
s = GBFRSaveData.open(save_path)

m1456 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1456)}
m1457 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1457)}
m1458 = {r.unit_id: list(s.get_values(r)) for r in s.find(id_type=1458)}
m1459 = {r.unit_id: list(s.get_values(r)) for r in s.find(id_type=1459)}
m1460 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1460)}

EMPTY = 0x887AE0B0
print('empty-state units sample (slot==0):')
n_empty_ok = n_empty_odd = 0
for u in sorted(m1456):
    slot = m1456[u]
    if slot != 0:
        continue
    th = m1457[u] & 0xFFFFFFFF
    mh, sh = m1458.get(u, [0, 0])
    ml, sl = m1459.get(u, [0, 0])
    rank = m1460.get(u, 0)
    ok = (th == EMPTY and (mh & 0xFFFFFFFF) == EMPTY and (sh & 0xFFFFFFFF) == EMPTY
          and (ml & 0xFFFFFFFF) == 0xFFFFFFFF and (sl & 0xFFFFFFFF) == 0xFFFFFFFF and rank == 0)
    if ok:
        n_empty_ok += 1
    else:
        n_empty_odd += 1
        if n_empty_odd <= 5:
            print(f'  ODD unit={u}: slot={slot} type=0x{th:08X} main=0x{mh&0xFFFFFFFF:08X} sub=0x{sh&0xFFFFFFFF:08X} ml={ml} sl={sl} rank={rank}')
print(f'  empty-state OK: {n_empty_ok}, odd: {n_empty_odd}')

# count records with slot != 0
n_occ = sum(1 for u, v in m1456.items() if v != 0)
print(f'  records with slot != 0: {n_occ}')

# how does the API find/set work for these?
r = s.find(id_type=1458, unit_id=19)
print()
print('1458 unit 19 records:', len(r))
if r:
    rec = r[0]
    print('  kind:', rec.kind, 'values:', list(s.get_values(rec)))
    # test set
    s.set_values(rec, [1, 2])
    print('  after set_values([1,2]):', list(s.get_values(rec)))
    s.set_values(rec, [0x3362730114 & 0xFFFFFFFF, 0x1716424242 & 0xFFFFFFFF])
    print('  restored:', list(s.get_values(rec)))
