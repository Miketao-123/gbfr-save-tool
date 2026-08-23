import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
s = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
def vm(idt): return {r.unit_id: s.get_first_value(r) for r in s.find(id_type=idt)}
m2701,m2703,m2704 = vm(2701),vm(2703),vm(2704)
m1701,m1702 = vm(1701),vm(1702)
print('2701 max slot count:', m2701.get(0))
# find ALL slots with the Dread Black Pincer gem
hits = [u for u,g in m2703.items() if (g&0xFFFFFFFF)==0x49434696]
print('可怕的漆黑钳蟹因子 (0x49434696) 所在槽位:', hits)
for slot in hits:
    idx = slot-30000
    print(f'  slot {slot}: 2704 lv={m2704.get(slot)} trait1=0x{m1701.get(120000000+idx*100):08X} tlv={m1702.get(120000000+idx*100)}')
# also check the 3 reward sigils presence
for name,h in [('漆黑之谊 In a Pinch',0x65F0420A),('相扑斗力 Sumo Force',0xB289A9AD),('可怕的漆黑钳蟹因子+',0x66CB28BA)]:
    hh = [u for u,g in m2703.items() if (g&0xFFFFFFFF)==h]
    print(f'{name} 0x{h:08X}: 槽位 {hh}')
print('哈希校验:', s.check_active_hash())
