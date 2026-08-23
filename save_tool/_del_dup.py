import sys, io, shutil, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
p = r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat'
save = GBFRSaveData.open(p)
EMPTY = 0x887AE0B0
del_slots = [31130, 33115]
def setf(idt, unit, val, kind):
    r = save.find_first(kind, idt, unit)
    if r is None:
        raise RuntimeError(f'缺少 {idt}/{unit}')
    save.set_first_value(r, val)
for slot in del_slots:
    idx = slot - 30000
    # sanity check
    r3 = save.find_first('uint', 2703, slot)
    if save.get_first_value(r3) != 0x49434696:
        print(f'警告:槽{slot} 不是可怕漆黑钳蟹因子,跳过'); continue
    setf(2702, slot, 0, 'uint')
    setf(2703, slot, EMPTY, 'uint')
    setf(2704, slot, 0, 'int')
    setf(2706, slot, EMPTY, 'uint')
    setf(2707, slot, 0, 'uint')
    setf(1701, 120000000+idx*100, EMPTY, 'uint')
    setf(1702, 120000000+idx*100, 1, 'int')
    setf(1701, 120000000+idx*100+1, EMPTY, 'uint')
    setf(1702, 120000000+idx*100+1, 1, 'int')
    print(f'已删除槽{slot}')
stamp = time.strftime('%Y%m%d_%H%M%S')
bak = p + f'.deldup_{stamp}'
shutil.copy2(p, bak)
save.save_over_original(update_hash=True, backup=False, validate=True, fsync=True)
print('备份:', bak)
# verify
s2 = GBFRSaveData.open(p)
m2703 = {r.unit_id: s2.get_first_value(r) for r in s2.find(id_type=2703)}
m2704 = {r.unit_id: s2.get_first_value(r) for r in s2.find(id_type=2704)}
m2701 = {r.unit_id: s2.get_first_value(r) for r in s2.find(id_type=2701)}
hits = [(u, m2704.get(u)) for u,g in m2703.items() if (g&0xFFFFFFFF)==0x49434696]
print('剩余可怕漆黑钳蟹因子:', hits)
print('2701 max slot:', m2701.get(0))
print('哈希校验:', s2.check_active_hash())
