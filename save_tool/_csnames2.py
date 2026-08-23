import sys, io, bisect
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool')
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
d = extract('system/table/text/cs/text.msg')
open(r'C:\Users\MikeT\Downloads\1.8.5\save_tool\_cs_text.msg','wb').write(d)
print('cs text.msg:', len(d), 'bytes')
import msgpack
obj = msgpack.unpackb(d, raw=False)
rows = obj.get('rows_', [])
targets = ['TXT_GEEN_300','TXT_GEEN_301','TXT_GEEN_302','TXT_GEEN_303','TXT_SKILL_300','TXT_SKILL_301','TXT_SKILL_302','TXT_SKILL_303','TXT_SKILL_SUMMARY_303','TXT_SKILL_EXPLAIN_303']
for r in rows:
    col = r.get('column_', {})
    kid = col.get('id_hash_','')
    if any(kid.startswith(t) for t in targets) and col.get('subid_hash_','') == '':
        print(f"{kid}: {col.get('text_','')}")
