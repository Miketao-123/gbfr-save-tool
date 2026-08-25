# -*- coding: utf-8 -*-
"""Check for both summon systems: old 3101-3115 (10100/10200) and new 1451-1460."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gbfr-save-editor', 'GBFR-Save-Editor-main', 'gbfr_editor', 'core'))
from gbfr_save import GBFRSaveData

save_path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames', 'SaveData1.dat')
s = GBFRSaveData.open(save_path)

print('=== new summon system id_types 1451-1460 ===')
for idt in range(1451, 1461):
    rows = s.find(id_type=idt)
    if rows:
        kind = rows[0].kind
        print(f'  {idt} ({kind}): {len(rows)} rows')
        for r in rows[:6]:
            vals = list(s.get_values(r))
            if len(vals) == 1:
                print(f'    unit={r.unit_id}: {vals[0]} (0x{vals[0] & 0xFFFFFFFF:08X})' if isinstance(vals[0], int) else f'    unit={r.unit_id}: {vals[0]}')
            else:
                print(f'    unit={r.unit_id}: {vals}')
    else:
        print(f'  {idt}: (none)')

print()
print('=== old summon system: full 10100/10200 list ===')
for r in s.find(id_type=3101):
    print(f'  unit={r.unit_id} 3101=0x{s.get_first_value(r) & 0xFFFFFFFF:08X}')
