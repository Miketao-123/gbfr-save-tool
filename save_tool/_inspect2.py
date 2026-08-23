import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CORE = r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core'
sys.path.insert(0, CORE)
from gbfr_save import GBFRSaveData
save = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')

DARK = 0x9FBA96D1
WEE  = 0xEE2559C6

# find item slots by hash value in 1801
id1801 = {r.unit_id: save.get_first_value(r) for r in save.find(id_type=1801)}
id1802 = {r.unit_id: save.get_first_value(r) for r in save.find(id_type=1802)}
print('=== crab item slots ===')
for name, h in [('Wee Pincer (小钳蟹)', WEE), ('Dark Wee Pincer (漆黑小钳蟹)', DARK)]:
    slots = [u for u,v in id1801.items() if (v & 0xFFFFFFFF) == h]
    print(f'{name} hash=0x{h:08X}: slots={slots}')
    for u in slots:
        print(f'   slot {u}: count(1802)={id1802.get(u)}')
    if not slots:
        print('   (not present in 1801)')

# also check 2102 (slot-style item id) and 2105 (quantity candidate)
print()
print('=== 2102/2103/2105 slot-style item records with crab hashes ===')
for idt in (2102,2103,2105):
    rows = save.find(id_type=idt)
    hits = []
    for r in rows:
        v = save.get_first_value(r)
        if (v & 0xFFFFFFFF) in (DARK, WEE):
            hits.append((r.unit_id, v))
    print(f'  id_type={idt}: {len(rows)} rows, crab hits={hits}')

# quest records
print()
print('=== QuestSystem 2570 (quest IDs) ===')
rows2570 = save.find(id_type=2570)
print(f'  2570 rows: {len(rows2570)}')
for r in rows2570[:5]:
    vals = save.get_values(r, 10)
    print(f'    unit_id={r.unit_id} kind={r.kind} count={r.value_count} vals={vals}')
