import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
s = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
# group records by id_type, count and kinds
from collections import defaultdict
bytype = defaultdict(lambda: defaultdict(int))
for r in s.records:
    bytype[r.id_type][r.kind] += 1
print('=== 存档所有 id_type ===')
for idt in sorted(bytype):
    kinds = ', '.join(f'{k}:{n}' for k,n in sorted(bytype[idt].items()))
    print(f'  {idt}: {kinds}')
