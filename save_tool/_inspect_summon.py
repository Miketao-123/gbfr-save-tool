# -*- coding: utf-8 -*-
"""Dump summon-related records (3101-3115) from the save."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gbfr-save-editor', 'GBFR-Save-Editor-main', 'gbfr_editor', 'core'))
from gbfr_save import GBFRSaveData

save_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames', 'SaveData1.dat')
s = GBFRSaveData.open(save_path)

print('=== summon-related id_types ===')
for idt in range(3101, 3120):
    rows = s.find(id_type=idt)
    if rows:
        kind = rows[0].kind
        print(f'  {idt} ({kind}): {len(rows)} rows')

print()
print('=== 3101/3102/3103/3104/3113 detail (first 40 units) ===')
import collections
units = set()
for idt in (3101, 3102, 3103, 3104, 3105, 3106, 3113):
    for r in s.find(id_type=idt):
        units.add(r.unit_id)
for u in sorted(units)[:40]:
    line = [f'unit={u}']
    for idt in (3101, 3102, 3103, 3104, 3105, 3106, 3113):
        recs = s.find(id_type=idt, unit_id=u)
        if recs:
            vals = list(s.get_values(recs[0])) if len(list(s.get_values(recs[0]))) > 1 else s.get_first_value(recs[0])
            line.append(f'{idt}={vals}')
    print('  ' + ', '.join(line))
