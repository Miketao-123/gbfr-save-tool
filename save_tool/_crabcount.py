import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
s = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
def vm(idt): return {r.unit_id: s.get_first_value(r) for r in s.find(id_type=idt)}
# 1) Dark Wee Pincer backpack count
id1801 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1801)}
id1802 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1802)}
slot440 = [u for u,v in id1801.items() if (v&0xFFFFFFFF)==0x9FBA96D1]
print('漆黑小钳蟹 背包槽:', slot440, '数量:', [id1802.get(u) for u in slot440])
# 2) quest state vectors (crab quests)
_, k2505 = (lambda r:(r, s.get_values(r)))(s.find_first('uint',2505,0))
_, k2550 = (lambda r:(r, s.get_values(r)))(s.find_first('uint',2550,0))
print('2505 count:', len(k2505), '2505 contains 290002:', 0x290002 in k2505)
# 3) 2506 and nearby quest counters
for idt in (2506, 2517, 2518, 2520):
    r = s.find_first('int', idt, 0) or s.find_first('uint', idt, 0) or s.find_first('bool', idt, 0)
    if r: print(f'{idt} {r.kind}: {s.get_values(r)}')
# 4) 蟹任务完成标志 (2554 for 2550 crab quests)
r2554 = s.find_first('bool', 2554, 0)
v2554 = s.get_values(r2554)
crab_idx = [i for i,v in enumerate(k2550) if (v&0xFFFFFFFF) in set(range(0x290002,0x290016))|{0x200001}]
print('2550 蟹任务索引:', crab_idx, '2554 flags:', [v2554[i] for i in crab_idx])
# 5) search for a 'captured crab count' - any int/uint single value == 20 near collection
print()
print('=== 搜索可能存"捕捉钳蟹数"的字段 ===')
# check ScenarioManager / collectible-ish types
for idt in (4201,4202,4501,4502,7201,7202,7203,7204,6101,6102,6901,6902):
    rows = s.find(id_type=idt)
    if rows:
        r = rows[0]
        vals = s.get_values(r, 5)
        print(f'  id_type={idt} {r.kind}[{r.value_count}]: {vals}')
