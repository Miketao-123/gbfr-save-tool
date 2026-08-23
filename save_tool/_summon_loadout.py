import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
from hashing import gbfr_hash
s = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
print('=== 3101-3115 (15条, 可能是召唤石) ===')
for idt in range(3101, 3116):
    rows = s.find(id_type=idt)
    if rows:
        vals = [(r.unit_id, s.get_first_value(r)) for r in rows[:15]]
        print(f'  {idt} {rows[0].kind}: {vals}')
print()
print('=== 9104-9129 (20条, 可能是装备方案/预设) ===')
for idt in range(9104, 9130):
    rows = s.find(id_type=idt)
    if rows:
        vals = [(r.unit_id, s.get_first_value(r)) for r in rows[:20]]
        print(f'  {idt} {rows[0].kind}: {vals}')
