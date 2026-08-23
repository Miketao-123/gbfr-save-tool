import sys, io, os, shutil, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
p = r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat'
save = GBFRSaveData.open(p)
EMPTY = 0x887AE0B0
slot = 33121; idx = slot - 30000
# sanity check: slot 33121 must be MY injected copy
rec2703 = save.find_first('uint', 2703, slot)
if save.get_first_value(rec2703) != 0x49434696:
    print('警告:槽 33121 不是预期的注入因子,中止。'); sys.exit(1)
def setf(idt, unit, val, kind):
    r = save.find_first(kind, idt, unit)
    save.set_first_value(r, val)
setf(2701, 0, 3806, 'uint')
setf(2702, slot, 0, 'uint')
setf(2703, slot, EMPTY, 'uint')
setf(2704, slot, 0, 'int')
setf(2706, slot, EMPTY, 'uint')
setf(2707, slot, 0, 'uint')
setf(1701, 120000000+idx*100, EMPTY, 'uint')
setf(1702, 120000000+idx*100, 1, 'int')
setf(1701, 120000000+idx*100+1, EMPTY, 'uint')
setf(1702, 120000000+idx*100+1, 1, 'int')
stamp = time.strftime('%Y%m%d_%H%M%S')
bak = p + f'.cleanup_{stamp}'
shutil.copy2(p, bak)
save.save_over_original(update_hash=True, backup=False, validate=True, fsync=True)
print('已移除注入的重复因子,备份:', bak)
# verify
s2 = GBFRSaveData.open(p)
m2703 = {r.unit_id: s2.get_first_value(r) for r in s2.find(id_type=2703)}
m2701 = {r.unit_id: s2.get_first_value(r) for r in s2.find(id_type=2701)}
m2704 = {r.unit_id: s2.get_first_value(r) for r in s2.find(id_type=2704)}
hits = [u for u,g in m2703.items() if (g&0xFFFFFFFF)==0x49434696]
print('清理后 2701:', m2701.get(0))
print('清理后可怕漆黑钳蟹因子槽位:', [(u, m2704.get(u)) for u in hits])
print('哈希校验:', s2.check_active_hash())
