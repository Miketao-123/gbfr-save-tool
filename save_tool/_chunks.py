import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool')
from gbfr_datai import parse_index, gbfr_file_hash
import bisect
idx = parse_index(r'D:\Steam\steamapps\common\Granblue Fantasy Relink\data.i')
hashes = idx['archive_file_hashes']
for p in ['system/table/skill.tbl','system/table/gem.tbl','system/table/skill_status.tbl']:
    h = gbfr_file_hash(p)
    i = bisect.bisect_left(hashes, h)
    if i < len(hashes) and hashes[i] == h:
        f2c = idx['file_to_chunk'][i]
        chunk = idx['chunks'][f2c[0]]
        print(f'{p}:')
        print(f'  file size={f2c[1]} off_in_chunk={f2c[2]} chunk_idx={f2c[0]}')
        print(f'  chunk: file_offset={chunk[0]} size={chunk[1]} uncomp={chunk[2]} data_file={chunk[4]}')
