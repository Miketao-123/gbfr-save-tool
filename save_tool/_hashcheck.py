import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from hashing import gbfr_hash, gbfr_hash_hex
# verify item hashes
for s in ['ITEM_60_0000','Wee Pincer','ITEM_60_0001','Dark Wee Pincer','ITEM_01_0000','ITEM_13_0000']:
    print(s, '->', gbfr_hash_hex(s))
print('expected Wee Pincer EE2559C6, Dark Wee Pincer 9FBA96D1')
