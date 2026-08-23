import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CORE = r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core'
sys.path.insert(0, CORE)
from gbfr_save import GBFRSaveData
save = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')

# dump all QuestSystem id_types 2501..2583
print('=== QuestSystem records (2501-2583) ===')
for idt in range(2501, 2584):
    rows = save.find(id_type=idt)
    if not rows:
        continue
    r0 = rows[0]
    vals = save.get_values(r0, 6)
    print(f'  id_type={idt} kind={r0.kind} rows={len(rows)} unit0_count={r0.value_count} sample={vals}')
