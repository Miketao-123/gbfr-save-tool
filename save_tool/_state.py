import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CORE = r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core'
sys.path.insert(0, CORE)
from gbfr_save import GBFRSaveData
save = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')

# dump full small state vectors 2501..2530
print('=== full QuestSystem state vectors 2501-2530 ===')
for idt in list(range(2501, 2531)):
    rows = save.find(id_type=idt)
    if not rows: continue
    r = rows[0]
    vals = save.get_values(r)
    if len(vals) <= 8:
        print(f'  {idt} {r.kind}[{len(vals)}] = {vals}')

# crab statue items (collection rewards)
print()
print('=== crab statue / reward items ===')
id1801 = {r.unit_id: save.get_first_value(r) for r in save.find(id_type=1801)}
id1802 = {r.unit_id: save.get_first_value(r) for r in save.find(id_type=1802)}
for name, h in [('Golden Crab Statue',0xFF1A207A),('Jet-Black Crab Statue',0x076A9F41)]:
    slots = [u for u,v in id1801.items() if (v & 0xFFFFFFFF) == h]
    print(f'  {name} 0x{h:08X}: slots={slots} counts={[id1802.get(u) for u in slots]}')
