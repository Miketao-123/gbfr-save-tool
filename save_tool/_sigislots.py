import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
save = GBFRSaveData.open(r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')
def vm(idt): return {r.unit_id: save.get_first_value(r) for r in save.find(id_type=idt)}
m2702, m2703, m2704, m2706, m2707 = vm(2702), vm(2703), vm(2704), vm(2706), vm(2707)
m1701, m1702 = vm(1701), vm(1702)
print('=== first 15 sigil slots (gem, 2704, 2707, 1701 trait, 1702 traitLv) ===')
for slot in range(30000, 30015):
    g = m2703.get(slot); lv = m2704.get(slot); fl = m2707.get(slot); worn = m2706.get(slot)
    th = m1701.get(120000000 + (slot-30000)*100); tl = m1702.get(120000000 + (slot-30000)*100)
    th2 = m1701.get(120000000 + (slot-30000)*100 + 1); tl2 = m1702.get(120000000 + (slot-30000)*100 + 1)
    print(f'  slot {slot}: gem=0x{g:08X} lv2704={lv} flags=0x{fl:X} worn=0x{worn:08X} | trait1=0x{th:08X} tlv1={tl} | trait2=0x{th2:08X} tlv2={tl2}')
# find empty sigil slots: gem id == EMPTY (0x887AE0B0) with valid 2702
print()
print('=== empty sigil slots (gem == EMPTY) count ===')
empty = [s for s,g in m2703.items() if g == 0x887AE0B0]
print('empty slots:', len(empty), 'first few:', empty[:10])
