import sys, io, shutil, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
p = r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat'
save = GBFRSaveData.open(p)
EMPTY = 0x887AE0B0
fixed = []
for slot in [31130, 31699]:
    idx = slot - 30000
    rec = save.find_first('uint', 1701, 120000000 + idx*100 + 1)
    old = save.get_first_value(rec)
    if (old & 0xFFFFFFFF) == 0x00000000:
        save.set_first_value(rec, EMPTY)
        fixed.append((slot, old))
    else:
        print(f'槽{slot}: 副词条已是 {old:08X},跳过')
stamp = time.strftime('%Y%m%d_%H%M%S')
bak = p + f'.fixblank_{stamp}'
shutil.copy2(p, bak)
save.save_over_original(update_hash=True, backup=False, validate=True, fsync=True)
print('已修复:', fixed)
print('备份:', bak)
s2 = GBFRSaveData.open(p)
m1701 = {r.unit_id: s2.get_first_value(r) for r in s2.find(id_type=1701)}
for slot in [31130, 31699]:
    idx = slot-30000
    print(f'槽{slot} 副词条现在: 0x{m1701.get(120000000+idx*100+1,0):08X}')
print('哈希校验:', s2.check_active_hash())
