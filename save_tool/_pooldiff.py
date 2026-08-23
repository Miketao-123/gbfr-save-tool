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
# skill_lot: Key hash, SkillId hash, Unk3 uint = 12
d = extract('system/table/skill_lot.tbl')
n = struct.unpack_from('<q', d, 0)[0]
lot_pool = {}
for i in range(n):
    b = 8 + i*12
    k = struct.unpack_from('<I', d, b)[0]
    s = struct.unpack_from('<I', d, b+4)[0]
    lot_pool.setdefault(k, []).append(s)
print('skill_lot 池数:', len(lot_pool))
# skill_type_lot Key=5 (昏厥Ⅴ＋) sub-lots
stl_lot5 = [0xf865a223, 0x8f952ac1, 0x46d6dfde, 0xd4078c7d]
pool5 = set()
for l in stl_lot5:
    pool5 |= set(lot_pool.get(l, []))
print('昏厥Ⅴ＋ 掉落池(skill_type_lot 5)大小:', len(pool5))
print('  含天星之雪(SKILL_324_00=0xA898E283):', 0xA898E283 in pool5)
# 对比作弊器规则的 137 个
sig = json.load(open('catalog_sigils_full.json', encoding='utf-8'))
for e in sig['sigils']:
    if e.get('internalId') == 'GEEN_004_24':
        tool_pool = set(gbfr_hash(x) for x in (e.get('allowedSecondaryTraitIds') or []))
        print('作弊器规则池大小:', len(tool_pool))
        print('  含天星之雪:', 0xA898E283 in tool_pool)
        # 差异
        only_tool = tool_pool - pool5
        only_game = pool5 - tool_pool
        print('  作弊器池里有但掉落池没有:', len(only_tool))
        print('  掉落池里有但作弊器没有:', len(only_game))
        # show a few from each
        cat = json.load(open('catalog.json', encoding='utf-8'))
        def names(s):
            out = []
            for h in list(s)[:6]:
                t = cat['traits'].get(str(h)) or cat['traits'].get(h)
                out.append((t or {}).get('cn') or (t or {}).get('en') or hex(h))
            return out
        print('  only_tool 示例:', names(only_tool))
        print('  only_game 示例:', names(only_game))
        break
