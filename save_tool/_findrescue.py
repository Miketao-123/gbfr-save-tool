import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
s = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
# 2550 crab quest indices
k2550 = s.get_values(s.find_first('uint',2550,0))
crab_idx = [i for i,v in enumerate(k2550) if (v&0xFFFFFFFF) in set(range(0x290002,0x290016))|{0x200001}]
print('蟹任务在2550的索引:', crab_idx)
# big quest vectors - check values at crab indices
for idt in (2513,2514,2515,2516,2552,2553,2582,2583):
    rec = s.find_first('uint',idt,0)
    if not rec: continue
    vals = s.get_values(rec)
    print(f'id_type={idt}: len={len(vals)}', end='')
    # sample at crab indices if within range
    samples = {}
    for i in crab_idx:
        if i < len(vals): samples[i] = vals[i]
    # also scan whole vector for values in 1..20 near crab region
    print(' crab-idx values:', samples)
# also 2506 context: is 2506 the rescue counter? check ALL ints = 20
print()
print('=== 寻找值为 20 的"救援计数"候选 ===')
# check 2510-2522 area and other quest vectors
for idt in (2505,2506,2510,2511,2512,2522):
    r = s.find_first('uint',idt,0) or s.find_first('int',idt,0)
    if r:
        v = s.get_values(r)
        # count 20s
        n20 = v.count(20)
        print(f'  {idt} {r.kind}[{len(v)}] 20-count={n20} sample20 idx: {[i for i,x in enumerate(v) if x==20][:10]}')
