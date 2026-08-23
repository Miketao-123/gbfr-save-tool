# -*- coding: utf-8 -*-
"""关联分析: 属性哈希 -> limit_bonus_param 星级数值"""
import sys, os, struct, bisect

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _decode_limit_bonus import extract_file, parse_header, decode_tbl
from gbfr_datai import parse_index

DATA_I = r'I:\STEAM\steamapps\common\Granblue Fantasy Relink\data.i'
idx = parse_index(DATA_I)
data_dir = os.path.dirname(DATA_I)

PARAM_HDR = '''add_column|FormatText1|hash_string
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
add_column|Unk21|int'''

CAT_HDR = '''add_column|Key|hash_string
add_column|MeditationWeightId|int
add_column|Weight|int'''


def load(name, hdr):
    raw = extract_file(idx, 'system/table/%s.tbl' % name, data_dir)
    cols = parse_header(hdr)
    for mode in ('both', 'none', 'only20'):
        c = cols if mode == 'both' else [x for x in cols if x[2] < (2, 0)] if mode == 'none' else [x for x in cols if not (x[2] == (2, 0) and x[0] == 'Unk21')]
        rows = decode_tbl(raw, c, name)
        if rows:
            return rows
    return None


params = load('limit_bonus_param', PARAM_HDR)
cats = load('limit_bonus_meditation_category', CAT_HDR)

print('=== category 表 (45行) ===')
for r in cats:
    print('  Key=0x%08X MeditationWeightId=%d Weight=%d' % (r['Key'] & 0xFFFFFFFF, r['MeditationWeightId'], r['Weight']))

# 目标属性哈希
TARGETS = {
    0xC4925BD7: '攻击力', 0x68B39018: '连锁爆发伤害', 0x45C65767: '暴击率',
    0x54929589: '治疗上限', 0x52A207B5: '体力', 0x43B7581D: '普攻伤害上限',
    0x4A4C093D: '奥义伤害上限', 0x4E42646B: '奥义伤害', 0x9C555433: '技能伤害上限',
    0x9A97C049: '技能伤害', 0x6CB38EF3: '昏厥力',
}
print()
print('=== param 表中与属性哈希匹配的行 ===')
for r in params:
    k = r['Key'] & 0xFFFFFFFF
    if k in TARGETS:
        lvs = [r['Lv%dValue' % i] for i in range(1, 11)]
        print('  0x%08X %-8s mult=%d unk19=%d  Lv1..10=%s' % (
            k, TARGETS[k], r['DisplayNumberMultiplier'], r['Unk19'],
            ', '.join('%g' % v for v in lvs)))
