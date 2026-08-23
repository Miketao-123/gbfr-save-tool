import sys, io, bisect, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_datai import parse_index, gbfr_file_hash
from hashing import gbfr_hash
import lz4.block, json
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
def parse_rows(d, rowsize, cols):
    n = struct.unpack_from('<q', d, 0)[0]
    out = []
    for i in range(n):
        b = 8 + i*rowsize
        row = []
        off = b
        for c in cols:
            if c == 'hash': row.append(struct.unpack_from('<I', d, off)[0]); off += 4
            elif c == 'uint': row.append(struct.unpack_from('<I', d, off)[0]); off += 4
        out.append(row)
    return out
# skill_type_lot: 6 hash + 6 uint + Key uint = 52
stl = parse_rows(extract('system/table/skill_type_lot.tbl'), 52, ['hash']*6 + ['uint']*6 + ['uint'])
print('skill_type_lot rows:', len(stl))
for r in stl:
    key = r[12]
    lots = r[0:6]; chances = r[6:12]
    print(f'  Key={key}: lots={[hex(x) for x in lots]} chances={chances}')
# gem_mix: 5 hash + Key uint = 24
gm = parse_rows(extract('system/table/gem_mix.tbl'), 24, ['hash']*5 + ['uint'])
print()
print('gem_mix rows:', len(gm))
for r in gm:
    print(f'  Key={r[5]}: tierMaps={[hex(x) for x in r[0:5]]}')
