import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
save = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')

print('=== GemManager record counts ===')
for idt in range(2701, 2709):
    rows = save.find(id_type=idt)
    if rows:
        kinds = set(r.kind for r in rows)
        print(f'  {idt}: {len(rows)} rows, kinds={kinds}')

print()
print('=== look for known sigils (Crabby Resonance 0x1C4D37E4, etc.) ===')
# gem id is in 2703 (value) per catalog; check structure: find records whose value == sigil hash
for idt in (2703, 2704, 2705, 2706, 2707, 2708):
    rows = save.find(id_type=idt)
    hits = []
    for r in rows:
        v = save.get_first_value(r)
        if (v & 0xFFFFFFFF) in (0x1C4D37E4, 0xF8FEF304, 0x82F1E7E4):
            hits.append((r.unit_id, v))
    if hits:
        print(f'  id_type={idt}: crab-sigil hits: {hits}')

print()
print('=== sample: first 12 records of 2703 (gem id) with unit_id + value ===')
rows = save.find(id_type=2703)
for r in rows[:12]:
    vals = save.get_values(r, 4)
    print(f'  unit_id={r.unit_id} kind={r.kind} count={r.value_count} vals={vals}')
