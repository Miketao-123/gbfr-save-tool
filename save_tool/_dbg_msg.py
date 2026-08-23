import sys, io, bisect
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool')
from gbfr_datai import parse_index, gbfr_file_hash
idx = parse_index(r'D:\Steam\steamapps\common\Granblue Fantasy Relink\data.i')
hashes = idx['archive_file_hashes']
ext = idx['external_file_hashes']
for p in ['system/table/text/en/text_uskill.msg','system/table/text/cs/text_uskill.msg','system/table/text/en/text.msg']:
    h = gbfr_file_hash(p)
    ia = bisect.bisect_left(hashes, h)
    ie = bisect.bisect_left(ext, h)
    in_a = ia < len(hashes) and hashes[ia] == h
    in_e = ie < len(ext) and ext[ie] == h
    print(f'{p}: hash={h:016X} in_archive={in_a} in_external={in_e}')
