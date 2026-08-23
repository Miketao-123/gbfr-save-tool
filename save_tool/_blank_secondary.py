import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
s = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
m2703 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=2703)}
m1701 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1701)}
m1702 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1702)}
EMPTY = 0x887AE0B0
zero2, empty2, real2, other2 = [], [], [], []
for u, g in m2703.items():
    if (g & 0xFFFFFFFF) == EMPTY: continue  # empty slot
    idx = u - 30000
    t2 = m1701.get(120000000 + idx*100 + 1)
    if t2 is None: continue
    t2 &= 0xFFFFFFFF
    if t2 == 0x00000000: zero2.append(u)
    elif t2 == EMPTY: empty2.append(u)
    elif t2 != 0: real2.append((u, t2))
    else: other2.append(u)
print(f'副词条=0x00000000 的因子槽(显示空白副词条): {len(zero2)} 个')
print('  ', zero2)
print(f'副词条=0x887AE0B0(正确空) 的因子槽: {len(empty2)} 个')
print(f'副词条=真实词条 的因子槽: {len(real2)} 个')
print(f'其他: {len(other2)} 个')
# also check trait1 values for 0
print()
print('主词条=0x00000000 的因子槽(可能也有问题):', [u for u,g in m2703.items() if (g&0xFFFFFFFF)!=EMPTY and (m1701.get(120000000+(u-30000)*100,0)&0xFFFFFFFF)==0])
