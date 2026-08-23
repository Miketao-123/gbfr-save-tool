import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
save = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
def vm(idt): return {r.unit_id: save.get_first_value(r) for r in save.find(id_type=idt)}
m2701 = vm(2701); m2702 = vm(2702); m2703 = vm(2703); m2704 = vm(2704); m2706 = vm(2706); m2707 = vm(2707)
m1701 = vm(1701); m1702 = vm(1702)
print('2701 max slot records:', {u:v for u,v in m2701.items()})
# check the candidate empty slot 33119 structure
for slot in [33114, 33118, 33119, 33120]:
    idx = slot - 30000
    print(f'slot {slot}: 2702={m2702.get(slot)} 2703=0x{m2703.get(slot,0):08X} 2704={m2704.get(slot)} 2706=0x{m2706.get(slot,0):08X} 2707=0x{m2707.get(slot,0):X} | 1701[0]=0x{m1701.get(120000000+idx*100,0):08X} 1702[0]={m1702.get(120000000+idx*100)} | 1701[1]=0x{m1701.get(120000000+idx*100+1,0):08X} 1702[1]={m1702.get(120000000+idx*100+1)}')
# what's the highest USED slot?
used = [s for s,g in m2703.items() if g != 0x887AE0B0]
print('highest used slot:', max(used), 'count used:', len(used))
