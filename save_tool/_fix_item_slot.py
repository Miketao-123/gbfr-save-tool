# -*- coding: utf-8 -*-
"""修复杀戮型脉冲组件(槽350)缺失的物品登记字段 1803/1804,并自增序列号计数器 1805。"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gbfr_cheat_tool as gct

path = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames', 'SaveData1.dat')
save = gct.GBFRSaveData.open(path)

m1801 = {r.unit_id: save.get_first_value(r) for r in save.find(id_type=1801)}
slot = next((u for u, h in m1801.items() if (h & 0xFFFFFFFF) == 0x04C18EEC), None)
if slot is None:
    print('[错误] 存档中找不到杀戮型脉冲组件'); sys.exit(1)

print(f'修复前 槽{slot}: 1801=0x{m1801[slot] & 0xFFFFFFFF:08X} '
      f'1802={save.get_first_value(save.find_first("int", 1802, slot))} '
      f'1803={save.get_first_value(save.find_first("uint", 1803, slot))} '
      f'1804={save.get_first_value(save.find_first("uint", 1804, slot))} '
      f'1805={save.get_first_value(save.find_first("uint", 1805, 0))}')

new_serial = save.get_first_value(save.find_first('uint', 1805, 0)) + 1
gct.set_first(save, 1803, slot, 12, 'uint')
gct.set_first(save, 1804, slot, new_serial, 'uint')
gct.set_first(save, 1805, 0, new_serial, 'uint')

bak = gct.save_and_backup(save, path, 'item_fix')
print(f'[完成] 槽{slot} 已修复: 1803=12 1804={new_serial} 1805={new_serial} 备份:{os.path.basename(bak)}')

# 验证
s2 = gct.GBFRSaveData.open(path)
print(f'验证: 1802={s2.get_first_value(s2.find_first("int", 1802, slot))} '
      f'1803={s2.get_first_value(s2.find_first("uint", 1803, slot))} '
      f'1804={s2.get_first_value(s2.find_first("uint", 1804, slot))} '
      f'1805={s2.get_first_value(s2.find_first("uint", 1805, 0))} '
      f'校验和={s2.check_active_hash()}')
