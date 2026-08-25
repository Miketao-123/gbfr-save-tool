# -*- coding: utf-8 -*-
"""Deep-dump one real summon slot (unit 10109) and empty ones."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gbfr-save-editor', 'GBFR-Save-Editor-main', 'gbfr_editor', 'core'))
from gbfr_save import GBFRSaveData

save_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames', 'SaveData1.dat')
s = GBFRSaveData.open(save_path)

for u in (10100, 10109, 10110):
    print(f'=== unit {u} ===')
    for idt in (3101, 3102, 3105, 3106, 3107, 3109, 3110, 3111, 3112, 3113, 3114, 3115):
        recs = s.find(id_type=idt, unit_id=u)
        if recs:
            r = recs[0]
            vals = list(s.get_values(r))
            if len(vals) == 1:
                print(f'  {idt} ({r.kind}): {vals[0]} (0x{vals[0] & 0xFFFFFFFF:08X})' if isinstance(vals[0], int) else f'  {idt} ({r.kind}): {vals[0]}')
            else:
                print(f'  {idt} ({r.kind}): {vals}')
    print()

# what units exist with non-empty 3101?
print('=== non-empty summon slots (3101 != EMPTY) ===')
for r in s.find(id_type=3101):
    v = s.get_first_value(r)
    if (v & 0xFFFFFFFF) != 0x887AE0B0:
        print(f'  unit={r.unit_id} 3101=0x{v & 0xFFFFFFFF:08X}')

# roster 1301
print()
print('=== roster 1301 (unit_id-10000 -> chara hash) ===')
for r in s.find(id_type=1301):
    v = s.get_first_value(r)
    print(f'  group {r.unit_id - 10000}: 0x{v & 0xFFFFFFFF:08X}')
