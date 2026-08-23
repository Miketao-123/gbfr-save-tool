import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
orig = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat.crab_backup_20260814_101032')
cur  = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
def snap(s):
    out = {}
    for r in s.records:
        if r.id_type in (2505,2506,2510,2511,2512,2522,2550,2551,2554,2555,2560,2561,2570,2571,2574,2575,2576,2577,2580,2581):
            out[(r.id_type, r.unit_id)] = tuple(s.get_values(r))
    return out
so, sc = snap(orig), snap(cur)
print('=== 原始 vs 当前 的任务向量差异 ===')
for k in sorted(set(so)|set(sc)):
    a, b = so.get(k), sc.get(k)
    if a != b:
        # show differing positions
        if a is None or b is None:
            print(f'  {k}: {"新增" if a is None else "消失"}')
        else:
            diffs = [(i,x,y) for i,(x,y) in enumerate(zip(a,b)) if x!=y]
            print(f'  {k}: len {len(a)}->{len(b)}, {len(diffs)} diffs, first: {diffs[:5]}')
print()
print('=== 2506 原始:', orig.get_values(orig.find_first("int",2506,0)), ' 当前:', cur.get_values(cur.find_first("int",2506,0)))
# item counts
def items(s):
    m = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1801)}
    c = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1802)}
    return m, c
mo, co = items(orig); mc, cc = items(cur)
for name,h in [('小钳蟹',0xEE2559C6),('漆黑小钳蟹',0x9FBA96D1),('金色蟹像',0xFF1A207A),('漆黑蟹像',0x076A9F41)]:
    so_s = [u for u,v in mo.items() if (v&0xFFFFFFFF)==h]
    sc_s = [u for u,v in mc.items() if (v&0xFFFFFFFF)==h]
    print(f'{name}: 原始槽{so_s} 数{[co.get(u) for u in so_s]} | 当前槽{sc_s} 数{[cc.get(u) for u in sc_s]}')
