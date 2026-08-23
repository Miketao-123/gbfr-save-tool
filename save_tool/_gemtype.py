import sys, io, bisect, struct, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_datai import parse_index, gbfr_file_hash
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
# parse gem_type: Unk1 int + 9 hex_uint = 40
d = extract('system/table/gem_type.tbl')
n = struct.unpack_from('<q', d, 0)[0]
print('gem_type rows:', n)
for i in range(n):
    b = 8 + i*40
    vals = [struct.unpack_from('<I', d, b+j*4)[0] for j in range(10)]
    print(' ', [hex(x) for x in vals])
# where do TierMapIds appear? scan gem table rows for ItemTierId values matching
gems = json.load(open('system_table_gem.tbl.json', encoding='utf-8'))
tier_ids = set()
for g in gems:
    tier_ids.add(g['ItemTierId'])
print()
print('gem 表的 ItemTierId 种类:', len(tier_ids))
print('  ', [hex(t) for t in sorted(tier_ids)])
# does gem_mix TierMapId appear as gem ItemTierId?
mix_tiers = {0x8f43077b, 0xef392488, 0xe5c59ce5, 0x9d2645f3, 0xd5760555}
print('mix TierMapId 是否都在 gem.ItemTierId 中:', mix_tiers.issubset(tier_ids))
