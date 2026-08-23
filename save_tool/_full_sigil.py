import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
s = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
def vm(idt): return {r.unit_id: s.get_first_value(r) for r in s.find(id_type=idt)}
m2702,m2703,m2704,m2706,m2707,m2708 = vm(2702),vm(2703),vm(2704),vm(2706),vm(2707),vm(2708)
m1701,m1702 = vm(1701),vm(1702)
print('=== 3 份可怕漆黑钳蟹因子完整结构 ===')
for slot in [31130, 31699, 33115]:
    idx = slot-30000
    print(f'槽 {slot}:')
    print(f'  2702={m2702.get(slot)} 2703=0x{m2703.get(slot):08X} 2704={m2704.get(slot)} 2706=0x{m2706.get(slot):08X} 2707=0x{m2707.get(slot):X} 2708={m2708.get(slot)}')
    for ti in (0,1):
        print(f'  1701[{ti}]=0x{m1701.get(120000000+idx*100+ti,0):08X} 1702[{ti}]={m1702.get(120000000+idx*100+ti)}')
print()
print('2708 records:', {u:v for u,v in m2708.items()})
