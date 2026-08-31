# -*- coding: utf-8 -*-
"""Compare slot formats: crabs (known-good) vs target item; also find other save copies."""
import sys, os, io, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gbfr-save-editor', 'GBFR-Save-Editor-main', 'gbfr_editor', 'core'))
from gbfr_save import GBFRSaveData

base = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames')
p = os.path.join(base, 'SaveData1.dat')
s = GBFRSaveData.open(p)
m1801 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1801)}
m1802 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1802)}
m1803 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1803)}
m1804 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1804)}

import json
cat = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'catalog.json'), encoding='utf-8'))
items = cat['items']

print('=== 已知有效的物品槽格式 ===')
for name, h in [('漆黑小钳蟹', 0x9FBA96D1), ('小钳蟹', 0xEE2559C6), ('漆黑蟹像', 0x076A9F41),
                ('杀戮型脉冲组件', 0x04C18EEC)]:
    slots = [u for u, v in m1801.items() if (v & 0xFFFFFFFF) == h]
    for u in slots:
        e = items.get(str(h)) or items.get(h)
        print('%-10s 槽%-4d 1802=%-6d 1803=%-4d 1804=%-8d %s' % (
            name, u, m1802.get(u, 0), m1803.get(u, 0), m1804.get(u, 0), (e.get('cn') if e else '')))

print()
print('=== 1803 值分组样本 ===')
from collections import defaultdict
by1803 = defaultdict(list)
for u in sorted(m1801):
    by1803[m1803.get(u, 0)].append(u)
for v in sorted(by1803):
    us = by1803[v][:5]
    print(f'1803={v} ({len(by1803[v])} 槽) 示例:')
    for u in us:
        h = m1801[u] & 0xFFFFFFFF
        e = items.get(str(h)) or items.get(h)
        print('    槽%-4d 0x%08X 1802=%-6d 1804=%-8d %s' % (u, h, m1802.get(u, 0), m1804.get(u, 0),
              (e.get('cn') or e.get('en') or e.get('id')) if e else '?'))

print()
print('=== 寻找其它存档副本 ===')
# 常见其它位置
cands = []
for pat in [os.path.join(base, 'SaveData*.dat'), os.path.join(base, '..', '*.dat'),
            os.path.join(os.path.expanduser('~'), 'Documents', '**', 'SaveData*.dat'),
            os.path.join(os.path.expanduser('~'), 'OneDrive', '**', 'SaveData*.dat')]:
    cands += glob.glob(pat, recursive=True)
seen = set()
for c in cands:
    if c not in seen:
        seen.add(c)
        print('  ', c, os.path.getsize(c) if os.path.exists(c) else '')
