import sys, io, struct
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, r'C:\Users\MikeT\Downloads\1.8.5\save_tool\gbfr-save-editor\GBFR-Save-Editor-main\gbfr_editor\core')
from hashing import gbfr_hash
data = open(r'D:\Steam\steamapps\common\Granblue Fantasy Relink\data.i','rb').read()
# candidate table paths
paths = [
    'system/table/skill.tbl', 'system/table/skill_status.tbl', 'system/table/gem.tbl',
    'system/table/chara_gem.tbl', 'system/table/skill_level_lot.tbl', 'system/table/skill_lot.tbl',
    'system/table/skill_type_lot.tbl', 'system/table/weapon_skill_level.tbl',
    'system/table/gem_rare.tbl', 'system/table/gem_ticket.tbl', 'system/table/gem_sell.tbl',
    'system/table/gem_mix.tbl', 'system/table/gem_mix_rupi.tbl', 'system/table/gem_mix_success.tbl',
    'system/table/ability.tbl', 'system/table/constant.tbl',
]
def find_u32(h):
    b = struct.pack('<I', h & 0xFFFFFFFF)
    return data.find(b)
for p in paths:
    h = gbfr_hash(p)
    idx = find_u32(h)
    print(f'{h:08X}  {idx!s:>8}  {p}')
