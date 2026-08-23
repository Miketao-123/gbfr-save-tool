import sys, io, bisect, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool')
from gbfr_datai import parse_index, gbfr_file_hash
import lz4.block
idx = parse_index(r'D:\Steam\steamapps\common\Granblue Fantasy Relink\data.i')
hashes = idx['archive_file_hashes']
def extract(path):
    h = gbfr_file_hash(path)
    i = bisect.bisect_left(hashes, h)
    if i >= len(hashes) or hashes[i] != h:
        print('  not found', path); return None
    f2c = idx['file_to_chunk'][i]; chunk = idx['chunks'][f2c[0]]
    print(f'  {path}: chunk={f2c[0]} data_file={chunk[4]} off={chunk[0]} size={chunk[1]} uncomp={chunk[2]} fsize={f2c[1]} decoff={f2c[2]}')
    with open(rf'D:\Steam\steamapps\common\Granblue Fantasy Relink\data.{chunk[4]}','rb') as f:
        f.seek(chunk[0]); raw = f.read(chunk[1])
    print('  read', len(raw))
    if chunk[2] != chunk[1]:
        raw = lz4.block.decompress(raw, uncompressed_size=chunk[2])
        print('  decompressed', len(raw))
    out = raw[f2c[2]:f2c[2]+f2c[1]]
    print('  file bytes', len(out))
    return out
for lang, name in [('en','text_uskill'),('cs','text_uskill'),('en','text')]:
    p = f'system/table/text/{lang}/{name}.msg'
    d = extract(p)
    if d:
        fn = rf'C:\Users\MikeT\Downloads\1.8.5\save_tool\_{lang}_{name}.msg'
        open(fn,'wb').write(d)
        print('  saved', fn)
