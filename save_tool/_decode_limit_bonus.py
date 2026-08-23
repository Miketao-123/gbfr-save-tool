# -*- coding: utf-8 -*-
"""提取并解码 limit_bonus_param.tbl 和 limit_bonus_meditation_category.tbl"""
import sys, os, struct, bisect, json

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gbfr_datai import parse_index, gbfr_file_hash
from _extract_chara_names import lz4_decompress

DATA_I = r'I:\STEAM\steamapps\common\Granblue Fantasy Relink\data.i'


def extract_file(idx, path, data_dir):
    h = gbfr_file_hash(path)
    hashes = idx['archive_file_hashes']
    i = bisect.bisect_left(hashes, h)
    if i >= len(hashes) or hashes[i] != h:
        return None
    f2c = idx['file_to_chunk'][i]
    chunk = idx['chunks'][f2c[0]]
    with open(os.path.join(data_dir, 'data.%d' % chunk[4]), 'rb') as f:
        f.seek(chunk[0]); raw = f.read(chunk[1])
    if chunk[2] != chunk[1]:
        raw = lz4_decompress(raw, chunk[2])
    return raw[f2c[2]:f2c[2] + f2c[1]]


SIZES = {'hash_string': 4, 'int': 4, 'float': 4, 'int64': 8, 'short': 2, 'ushort': 2,
         'byte': 1, 'sbyte': 1, 'string': 8, 'raw_string': 8}


def parse_header(text):
    """解析 headers 文本 -> [(name, type)] 及版本分段"""
    cols = []
    ver = 0.0
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('//'):
            continue
        if line.startswith('set_min_version|'):
            v = line.split('|')[1].strip()
            try:
                ver = tuple(int(x) for x in v.split('.'))
            except ValueError:
                ver = (0,)
        elif line.startswith('reset_min_version'):
            ver = (0,)
        elif line.startswith('add_column|'):
            parts = line.split('|')
            cols.append((parts[1], parts[2].strip(), ver))
    return cols


def decode_tbl(raw, cols, name):
    """按列定义解码 tbl;cols = [(name, type, min_version)]"""
    n = struct.unpack_from('<Q', raw, 0)[0]
    row_size = sum(SIZES[c[1]] for c in cols)
    body = raw[8:]
    if len(body) % row_size != 0:
        # 尝试去掉 2.0.0 版本列
        for drop in range(1, 4):
            cols2 = [c for c in cols if c[2] < 2.0]
            # 上面的 drop 逻辑不对,单独处理
            pass
        print('  [%s] 大小不匹配: body=%d row_size=%d (余数 %d)' % (name, len(body), row_size, len(body) % row_size))
        return None
    rows = []
    off = 0
    for r in range(n):
        row = {}
        for cname, ctype, _ in cols:
            sz = SIZES[ctype]
            if ctype == 'float':
                v = struct.unpack_from('<f', body, off)[0]
            elif ctype == 'hash_string':
                v = struct.unpack_from('<I', body, off)[0]
            elif ctype == 'int':
                v = struct.unpack_from('<i', body, off)[0]
            elif ctype == 'int64':
                v = struct.unpack_from('<q', body, off)[0]
            elif ctype in ('byte', 'sbyte', 'short', 'ushort'):
                fmt = {'byte': '<B', 'sbyte': '<b', 'short': '<h', 'ushort': '<H'}[ctype]
                v = struct.unpack_from(fmt, body, off)[0]
            else:
                v = struct.unpack_from('<q', body, off)[0]
            row[cname] = v
            off += sz
        rows.append(row)
    return rows


def main():
    idx = parse_index(DATA_I)
    data_dir = os.path.dirname(DATA_I)
    param_raw = extract_file(idx, 'system/table/limit_bonus_param.tbl', data_dir)
    cat_raw = extract_file(idx, 'system/table/limit_bonus_meditation_category.tbl', data_dir)
    med_raw = extract_file(idx, 'system/table/limit_bonus_meditation.tbl', data_dir)
    print('limit_bonus_param.tbl bytes:', len(param_raw) if param_raw else None)
    print('limit_bonus_mediation_category.tbl bytes:', len(cat_raw) if cat_raw else None)
    print('limit_bonus_meditation.tbl bytes:', len(med_raw) if med_raw else None)
    if cat_raw is None:
        # 调试: hash 是否在索引中
        h = gbfr_file_hash('system/table/limit_bonus_meditation_category.tbl')
        import bisect
        hashes = idx['archive_file_hashes']
        i = bisect.bisect_left(hashes, h)
        print('category hash 0x%016X 在索引中: %s (i=%d, hashes[%d]=0x%016X)' % (
            h, i < len(hashes) and hashes[i] == h, i, i,
            hashes[i] if i < len(hashes) else 0))

    headers = {
        'param': '''add_column|FormatText1|hash_string
add_column|FormatText2|hash_string
add_column|FormatText3|hash_string
add_column|Lv1Value|float
add_column|Lv2Value|float
add_column|Lv3Value|float
add_column|Lv4Value|float
add_column|Lv5Value|float
add_column|Lv6Value|float
add_column|Lv7Value|float
add_column|Lv8Value|float
add_column|Lv9Value|float
add_column|Lv10Value|float
add_column|Key|hash_string
set_min_version|2.0.0
add_column|Unk20|int
reset_min_version
add_column|NameFormat|hash_string
add_column|FullName|hash_string
add_column|LimitBonusParamTypeId|int
add_column|DisplayNumberMultiplier|int
add_column|Unk19|int
set_min_version|2.0.0
add_column|Unk21|int''',
        'category': '''add_column|Key|hash_string
add_column|MeditationWeightId|int
add_column|Weight|int''',
        'meditation': '''add_column|NumMasteries1|int
add_column|NumMasteries2|int
add_column|NumMasteries3|int
add_column|NumMasteriesWeight1|int
add_column|NumMasteriesWeight2|int
add_column|NumMasteriesWeight3|int
add_column|OvermasteryTypeTitle|hash_string
add_column|OvermasteryTypeDescription|hash_string
add_column|MeditationCategoryId|int
add_column|MSPCost|int
add_column|Unk11|int''',
    }
    for key, raw, hdr in (('param', param_raw, headers['param']),
                          ('category', cat_raw, headers['category']),
                          ('meditation', med_raw, headers['meditation'])):
        if raw is None:
            continue
        cols = parse_header(hdr)
        # 尝试带/不带 2.0.0 版本列
        for mode in ('both', 'none', 'only20'):
            if mode == 'both':
                c = cols
            elif mode == 'none':
                c = [x for x in cols if x[2] < 2.0]
            else:
                c = [x for x in cols if not (x[2] == 2.0 and x[0] == 'Unk21')]
            rows = decode_tbl(raw, c, key)
            if rows:
                print('=== %s (%s 模式, %d 行) ===' % (key, mode, len(rows)))
                for r in rows[:60]:
                    print('   ', r)
                break


if __name__ == '__main__':
    main()
