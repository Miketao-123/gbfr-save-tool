import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from hashing import gbfr_hash
chars = {}
for n in range(0, 4000, 100):
    gid = f'PL{n:04d}'
    chars[gbfr_hash(gid)] = gid
json.dump(chars, open(r'catalog_chars.json','w',encoding='utf-8'))
print('chars:', len(chars))
# verify PL0000 hash
print('PL0000 -> 0x%08X' % gbfr_hash('PL0000'))
