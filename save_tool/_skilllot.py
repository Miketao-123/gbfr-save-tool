import sys, io, bisect, struct, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_datai import parse_index, gbfr_file_hash
from hashing import gbfr_hash
import lz4.block
idx = parse_index(r'D:\Steam\steamapps\common\Granblue Fantasy Relink\data.i')
hashes = idx['archive_file_hashes']
def extract(path):
    h = gbfr_file_hash(path)
    i = bisect.bisect_left(hashes, h)
    if i >= len(hashes) or hashes[i] != h: return None
    f2c = idx['file_to_chunk'][i]; chunk = idx['chunks'][f2c[0]]
    with open(rf'D:\Steam\steamapps\common\Granblue Fantasy Relink\data.{chunk[4]}','rb') as f:
        f.seek(chunk[0]); raw = f.read(chunk[1])
    if chunk[2] != chunk[1]: raw = lz4.block.decompress(raw, uncompressed_size=chunk[2])
    return raw[f2c[2]:f2c[2]+f2c[1]]
d = extract('system/table/skill_lot.tbl')
n = struct.unpack_from('<q', d, 0)[0]
print('skill_lot rows:', n)
rows = []
for i in range(n):
    b = 8 + i*12
    rows.append((struct.unpack_from('<I', d, b)[0], struct.unpack_from('<I', d, b+4)[0], struct.unpack_from('<I', d, b+8)[0]))
# key values - what are the lot keys?
keys = sorted(set(r[0] for r in rows))
print('distinct lot keys:', len(keys))
print('sample keys:', [hex(k) for k in keys[:20]])
# try to identify lot 5: hash of "5"? "LOT_5"?
for cand in ['5', 'LOT_5', 'LOT5', 'SKILL_LOT_5', 'TYPE_5']:
    h = gbfr_hash(cand)
    if h in keys:
        print('lot key match:', cand, hex(h))
# check each key's pool for SKILL_324_00 (天星之雪 hash 0xA898E283)
snow = 0xA898E283
for k in sorted(keys):
    pool = [r[1] for r in rows if r[0]==k]
    if snow in pool:
        print(f'lot 0x{k:08X}: 含天星之雪 (SKILL_324_00), 池大小 {len(pool)}')
# what does the gem's "5" map to? print pools for keys that look small
print()
print('小 lot 池:')
small = sorted(keys)[:8]
for k in small:
    pool = [r[1] for r in rows if r[0]==k]
    print(f'  0x{k:08X}: {len(pool)} traits')
