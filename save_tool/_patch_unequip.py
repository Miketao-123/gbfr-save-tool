import re
p = r'gbfr_cheat_tool.py'
src = open(p, encoding='utf-8').read()
old = """    for act in ('sigils', 'equip', 'unequip', 'clear'):
        pp = pa.add_parser(act); pp.add_argument('chara')
        if act in ('equip',):
            pp.add_argument('sigil')"""
new = """    for act in ('sigils', 'equip', 'unequip', 'clear'):
        pp = pa.add_parser(act); pp.add_argument('chara')
        if act in ('equip', 'unequip'):
            pp.add_argument('sigil')"""
assert old in src
src = src.replace(old, new)
open(p, 'w', encoding='utf-8').write(src)
print('patched')
