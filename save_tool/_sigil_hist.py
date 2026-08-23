import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from gbfr_save import GBFRSaveData
for tag, p in [('原始(crab_backup)', r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat.crab_backup_20260814_101032'),
               ('当前', r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames\SaveData1.dat')]:
    s = GBFRSaveData.open(p)
    m2703 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=2703)}
    m2704 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=2704)}
    m1701 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1701)}
    m1702 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1702)}
    print(f'=== {tag} ===')
    for name,h in [('可怕漆黑钳蟹(301)',0x49434696),('漆黑之谊(302)',0x65F0420A),('相扑斗力(303)',0xB289A9AD),('可怕漆黑+',0x66CB28BA)]:
        slots = [u for u,g in m2703.items() if (g&0xFFFFFFFF)==h]
        info = []
        for u in slots:
            idx = u-30000
            t1 = m1701.get(120000000+idx*100); t2 = m1701.get(120000000+idx*100+1)
            info.append(f'槽{u} lv{m2704.get(u)} trait1=0x{t1:08X} trait2=0x{t2:08X}')
        print(f'  {name}: {info}')
