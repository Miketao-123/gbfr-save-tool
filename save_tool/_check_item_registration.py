# -*- coding: utf-8 -*-
"""Check item slot registration pattern: 1803/1804 meaning, ITEM_31 series, and SystemData."""
import sys, os, io
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
m1807 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1807)}

import json
cat = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'catalog.json'), encoding='utf-8'))
items = cat['items']

# 1) 1803 值的分布
from collections import Counter
c1803 = Counter(m1803.get(u, 0) for u in m1801)
c1807 = Counter(m1807.get(u, 0) for u in m1801)
print('1803 值分布:', dict(c1803))
print('1807 值分布:', dict(c1807))

# 2) ITEM_31 系列物品的 1802/1803/1804
print()
print('=== ITEM_31 系列全部物品 ===')
for u, h in sorted(m1801.items(), key=lambda kv: kv[0]):
    e = items.get(str(h)) or items.get(h)
    if e and str(e.get('id', '')).startswith('ITEM_31_'):
        print('  槽%-4d 0x%08X %-16s 1802=%-6d 1803=%-4d 1804=%-8d 1807=%d  %s' % (
            u, h & 0xFFFFFFFF, e.get('id'), m1802.get(u, 0), m1803.get(u, 0), m1804.get(u, 0),
            m1807.get(u, 0), e.get('cn') or e.get('en')))

# 3) 1803=0 或 1804=0 的槽(异常登记)
print()
print('=== 1803=0 或 1804=0 的槽(疑似未登记) ===')
for u in sorted(m1801):
    if m1803.get(u, 0) == 0 or m1804.get(u, 0) == 0:
        h = m1801[u] & 0xFFFFFFFF
        e = items.get(str(h)) or items.get(h)
        print('  槽%-4d 0x%08X 1802=%-6d 1803=%d 1804=%d  %s' % (
            u, h, m1802.get(u, 0), m1803.get(u, 0), m1804.get(u, 0),
            (e.get('cn') or e.get('en') or e.get('id')) if e else '?'))

# 4) SystemData.dat
print()
print('=== SystemData.dat ===')
sp = os.path.join(base, 'SystemData.dat')
if os.path.exists(sp):
    print('存在, %d 字节' % os.path.getsize(sp))
    try:
        sd = GBFRSaveData.open(sp)
        print('records:', len(sd.records))
        for idt in sorted({r.id_type for r in sd.records})[:30]:
            rows = sd.find(id_type=idt)
            print(f'  {idt} ({rows[0].kind}): {len(rows)} rows, sample {sd.get_first_value(rows[0])}')
    except Exception as e:
        print('解析失败:', e)
