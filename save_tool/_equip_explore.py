import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
from hashing import gbfr_hash
s = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
EMPTY = 0x887AE0B0
# 1) equipped sigils: 2706 worn-by != EMPTY
m2703 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=2703)}
m2706 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=2706)}
m2704 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=2704)}
equipped = [(u, m2706.get(u), m2704.get(u)) for u,g in m2703.items() if (g&0xFFFFFFFF)!=EMPTY and m2706.get(u)!=EMPTY]
print('=== 已装备的因子 (槽, 装备角色哈希, 等级) ===')
for u, worn, lv in equipped[:40]:
    print(f'  槽{u} worn=0x{worn:08X} lv={lv}')
print('总装备因子数:', len(equipped))
# 2) character hashes
chars = ['PL0000','PL0100','PL0200','PL0300','PL0400','PL0500','PL0600','PL0700','PL0800','PL0900','PL1000','PL1100','PL1200','PL1300','PL1400','PL1500','PL1600','PL1700','PL1800','PL1900','PL2000','PL2100','PL2200','PL2300']
print()
print('=== 角色哈希 ===')
chashes = {}
for c in chars:
    h = gbfr_hash(c)
    chashes[h] = c
    print(f'  {c} = 0x{h:08X}')
# which characters have equipped sigils
print()
print('=== 各角色装备的因子数 ===')
from collections import Counter
cnt = Counter(m2706.get(u) for u,g in m2703.items() if (g&0xFFFFFFFF)!=EMPTY and m2706.get(u)!=EMPTY)
for h, n in cnt.items():
    print(f'  0x{h:08X} ({chashes.get(h, "?")}): {n} 个')
