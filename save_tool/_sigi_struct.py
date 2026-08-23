import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
from hashing import gbfr_hash_hex
save = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')

def val_map(idt, kind):
    out = {}
    for r in save.find(id_type=idt):
        out[r.unit_id] = save.get_first_value(r)
    return out

slots = {30006: 'Crabby Resonance(钳蟹共鸣)', 33114: 'Crabvestment(钳蟹报恩)'}
m2703 = val_map(2703, 'uint'); m2704 = val_map(2704, 'int'); m2706 = val_map(2706,'uint'); m2707 = val_map(2707,'uint')
m1701 = val_map(1701, 'uint'); m1702 = val_map(1702, 'int')
for slot, name in slots.items():
    print(f'=== slot {slot} = {name} ===')
    print(f'  2703 gem_id   = 0x{m2703.get(slot,0):08X}')
    print(f'  2704 level    = {m2704.get(slot)}')
    print(f'  2706 worn_by  = 0x{m2706.get(slot,0):08X}')
    print(f'  2707 flags    = 0x{m2707.get(slot,0):08X}')
    # traits in 1701/1702 at this slot (may be multiple)
    for u, h in sorted(m1701.items()):
        if u == slot:
            print(f'  1701 trait    = 0x{h:08X} ({gbfr_hash_hex(str(h))}) lv={m1702.get(u)}')
    # also list all 1701 near this slot (index offset)
print()
print('=== 1701/1702 for slots 30000-30012 ===')
for slot in range(30000, 30013):
    h = m1701.get(slot); lv = m1702.get(slot)
    g = m2703.get(slot)
    print(f'  slot {slot}: gem=0x{g:08X} trait=0x{h:08X if h else 0} lv={lv}')
