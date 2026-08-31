# -*- coding: utf-8 -*-
"""Check ALL ItemManager fields for the target item (slot 350 / hash 0x04C18EEC)."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'gbfr-save-editor', 'GBFR-Save-Editor-main', 'gbfr_editor', 'core'))
from gbfr_save import GBFRSaveData

p = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames', 'SaveData1.dat')
s = GBFRSaveData.open(p)

# 1) 所有 ItemManager 相关 id_type 及其行数
print('=== ItemManager 相关 id_type ===')
for idt in range(1801, 1810):
    rows = s.find(id_type=idt)
    if rows:
        print(f'  {idt} ({rows[0].kind}): {len(rows)} rows, unit 范围 {min(r.unit_id for r in rows)}-{max(r.unit_id for r in rows)}')

# 2) 目标物品槽 350 的全部字段
print()
print('=== 槽 350 (杀戮型脉冲组件) 的全部记录 ===')
tgt = 0x04C18EEC
m1801 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1801)}
slots = [u for u, h in m1801.items() if (h & 0xFFFFFFFF) == tgt]
print('匹配槽位:', slots)
for u in slots:
    for idt in range(1801, 1810):
        recs = s.find(id_type=idt, unit_id=u)
        if recs:
            vals = list(s.get_values(recs[0]))
            print(f'  {idt} ({recs[0].kind}): {vals}')

# 3) 有没有第二个"数量"类字段(1803/1805/1807)与 1802 同时存在?
print()
print('=== 1802 vs 1803/1805/1807 对照(前10个有 1802 的槽) ===')
m1802 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1802)}
for u in sorted(m1802)[:10]:
    row = [f'unit{u} 1802={m1802[u]}']
    for idt in (1803, 1804, 1805, 1807):
        recs = s.find(id_type=idt, unit_id=u)
        if recs:
            row.append(f'{idt}={list(s.get_values(recs[0]))}')
    print('  ' + ' | '.join(row))
