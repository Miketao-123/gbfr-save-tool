import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
import gbfr_cheat_tool as gct
save = gct.GBFRSaveData.open(gct.DEFAULT_SAVE)
# 统计所有 id_type 及其 unit 分布
from collections import Counter
cnt = Counter()
units = {}
for r in save.records:
    cnt[r.id_type] += 1
    units.setdefault(r.id_type, set()).add(r.unit_id)
print('=== 所有 id_type 及数量 ===')
for idt, n in sorted(cnt.items()):
    us = units[idt]
    sample = ','.join(str(u) for u in sorted(us)[:12])
    print(f'  {idt}: {n} 条, units={len(us)} e.g.{sample}')
