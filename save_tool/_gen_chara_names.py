# -*- coding: utf-8 -*-
"""从已提取的游戏文本表生成 chara_names.json (PLxxxx -> {cn, en})。"""
import sys, json, os

try:
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
except Exception:
    pass
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _extract_chara_names import msgpack_load, dump_rows

base = os.path.dirname(os.path.abspath(__file__))
cn = {r[0][4:]: r[2] for r in dump_rows(msgpack_load(open(os.path.join(base, '_cs_text_chara.msg'), 'rb').read()))
      if r[0] and r[0].startswith('TXT_PL')}
en = {r[0][4:]: r[2] for r in dump_rows(msgpack_load(open(os.path.join(base, '_en_text_chara.msg'), 'rb').read()))
      if r[0] and r[0].startswith('TXT_PL')}

out = {}
for pl in sorted(set(cn) | set(en)):
    if pl == 'PL000B':  # dummy/LookDev 非真实角色
        continue
    e = {}
    if cn.get(pl):
        e['cn'] = cn[pl]
    if en.get(pl):
        e['en'] = en[pl]
    out[pl] = e

with open(os.path.join(base, 'chara_names.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('chara_names.json:', len(out), 'entries')
for pl, e in out.items():
    print('  %-8s %s' % (pl, e))
