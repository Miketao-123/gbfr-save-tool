import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from hashing import gbfr_hash
# what is 0x9A8AF295?
target = 0x9A8AF295
# try DLC characters and summon IDs
cands = []
for n in range(2400, 3000, 100):
    cands.append(f'PL{n}')
for n in range(0, 3000, 100):
    cands.append(f'SP{n}')
for n in range(0, 3000, 100):
    cands.append(f'SUMMON{n}')
for c in cands:
    if gbfr_hash(c) == target:
        print('FOUND:', c)
# also dump 3101 unit_id structure: what are 10100/10200?
print()
print('3101 unit_id 10100/10109 哈希:')
for u in [10100, 10109]:
    print(f'  unit {u}')
