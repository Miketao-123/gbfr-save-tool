import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CORE = r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core'
sys.path.insert(0, CORE)
from gbfr_save import GBFRSaveData

save = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
s = save.summary()
print('=== summary ===')
for k,v in s.items():
    print(f'  {k}: {v}')

print()
print('=== records containing crab item hashes ===')
DARK = 0x9FBA96D1   # Dark Wee Pincer ITEM_60_0001
WEE  = 0xEE2559C6   # Wee Pincer ITEM_60_0000
for rec in save.records:
    if rec.id_type in (1801,1802,1803,2101,2102,2103,2105) and rec.unit_id in (DARK, WEE):
        vals = save.get_values(rec, 8)
        print(f'  kind={rec.kind} id_type={rec.id_type} unit_id=0x{rec.unit_id:08X} count={rec.value_count} vals={vals}')

print()
print('=== all 1801/1802 unit_ids (first 40) ===')
for idt in (1801,1802):
    rows = save.find(id_type=idt)
    print(f'  id_type={idt}: {len(rows)} rows')
    for r in rows[:40]:
        vals = save.get_values(r, 4)
        print(f'    unit_id=0x{r.unit_id:08X} kind={r.kind} count={r.value_count} vals={vals}')
