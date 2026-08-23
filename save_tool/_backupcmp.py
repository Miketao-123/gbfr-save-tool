import sys, io, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
CORE = r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core'
sys.path.insert(0, CORE)
from gbfr_save import GBFRSaveData
base = r'C:\Users\MikeT\AppData\Local\GBFR\Saved\SaveGames'
for fn in ['SaveData1.dat','SaveData1_BackUp.dat','SaveData1_BackUp2.dat']:
    p = os.path.join(base, fn)
    try:
        s = GBFRSaveData.open(p)
        v2506 = s.get_values(s.find_first('int',2506))
        v2505 = s.get_values(s.find_first('uint',2505))
        v2517 = s.get_values(s.find_first('uint',2517))
        v2518 = s.get_values(s.find_first('uint',2518))
        v2520 = s.get_values(s.find_first('bool',2520))
        # dark crab + statue counts
        id1802 = {r.unit_id: s.get_first_value(r) for r in s.find(id_type=1802)}
        print(f'{fn}:')
        print(f'   2506={v2506}  2517={v2517}  2518={v2518}  2520={v2520}')
        print(f'   2505 count={len(v2505)}')
        print(f'   slot440(DarkWee)= {id1802.get(440)}  slot426(JetBlackStatue)= {id1802.get(426)}  slot245(Wee)= {id1802.get(245)}  slot122(GoldStatue)= {id1802.get(122)}')
    except Exception as e:
        print(f'{fn}: ERR {e}')
