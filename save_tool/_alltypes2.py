import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
from collections import defaultdict
s = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
bytype = defaultdict(lambda: defaultdict(int))
for r in s.records:
    bytype[r.id_type][r.kind] += 1
lines = []
for idt in sorted(bytype):
    kinds = ', '.join(f'{k}:{n}' for k,n in sorted(bytype[idt].items()))
    lines.append(f'{idt}: {kinds}')
open(r'C:\Users\MikeT\Downloads\1.8.5\save_tool\_idtypes.txt','w',encoding='utf-8').write('\n'.join(lines))
print('saved', len(lines), 'lines')
