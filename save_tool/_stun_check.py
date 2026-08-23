import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
gem = json.load(open('catalog_gem.json', encoding='utf-8'))
# find sigils whose primary trait name contains 昏厥/Stun
traits = gem['trait_info']
sigils = gem['sigil_info']
print('=== 主词条为 昏厥/Stun 的因子 ===')
for hk, e in sigils.items():
    p = e.get('primary')
    pt = traits.get(str(p), {})
    name = (pt.get('cn') or pt.get('name') or '')
    if '昏厥' in name or 'Stun' in name:
        print(f'  因子:{e.get("cn") or e.get("name")}  hash=0x{int(hk)&0xFFFFFFFF:08X}  主词条:{name}  maxLv:{pt.get("max_level")}  副词条:{"固定0x%08X" % e.get("secondary") if (e.get("secondary") or 0x887AE0B0) != 0x887AE0B0 else "无(可自选)"}')
print()
print('=== 词条 天星之雪 ===')
for hk, e in traits.items():
    n = (e.get('cn') or '') + (e.get('name') or '')
    if '天星之雪' in n or 'Snow' in n:
        print(f'  天星之雪 -> 0x{int(hk)&0xFFFFFFFF:08X}  {e.get("name")} maxLv:{e.get("max_level")}')
