# -*- coding: utf-8 -*-
"""从提取的游戏数据构建 物品/因子/词条/召唤石 目录 JSON。"""
import io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
    'gbfr-save-editor', 'GBFR-Save-Editor-main', 'gbfr_editor', 'core'))
from hashing import gbfr_hash
import msgpack

BASE = os.path.dirname(os.path.abspath(__file__))

def load_msg(fn):
    return msgpack.unpackb(open(os.path.join(BASE, fn), 'rb').read(), raw=False)

def build_name_map(lang):
    """id_hash_ -> (subid, text) 列表"""
    obj = load_msg(f'_{lang}_text.msg')
    m = {}
    for r in obj.get('rows_', []):
        col = r.get('column_', {})
        kid = col.get('id_hash_', '')
        sub = col.get('subid_hash_', '')
        txt = col.get('text_', '')
        if not sub:
            m[kid] = txt
    return m

en = build_name_map('en')
cs = build_name_map('cs')

# ---- items ----
# TXT_ITEM_XX_YYYY -> name; item hash = gbfr_hash("ITEM_XX_YYYY")
items = {}
for key, name in en.items():
    if key.startswith('TXT_ITEM_') and not key.startswith('TXT_ITEM_INFO'):
        gid = key[len('TXT_'):]
        if gid.startswith('ITEM_'):
            h = gbfr_hash(gid)
            items[h] = {'id': gid, 'en': name, 'cn': cs.get(key, '')}

# ---- sigils (GEEN) ----
sigils = {}
for key, name in en.items():
    if key.startswith('TXT_GEEN_'):
        gid = key[len('TXT_'):]
        h = gbfr_hash(gid)
        sigils[h] = {'id': gid, 'en': name, 'cn': cs.get(key, '')}

# ---- traits (SKILL) ----
traits = {}
for key, name in en.items():
    if key.startswith('TXT_SKILL_') and not key.startswith('TXT_SKILL_SUMMARY') and not key.startswith('TXT_SKILL_EXPLAIN') and not key.startswith('TXT_SKILL_LEVEL'):
        gid = key[len('TXT_'):]
        if gid.startswith('SKILL_'):
            h = gbfr_hash(gid)
            traits[h] = {'id': gid, 'en': name, 'cn': cs.get(key, '')}

out = {
    'items': items,
    'sigils': sigils,
    'traits': traits,
}
with open(os.path.join(BASE, 'catalog.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print(f'items={len(items)} sigils={len(sigils)} traits={len(traits)} -> catalog.json')

# ---- gem table merge: sigil -> primary/secondary trait hashes + legality ----
gems = json.load(open(os.path.join(BASE, 'system_table_gem.tbl.json'), encoding='utf-8'))
skills = json.load(open(os.path.join(BASE, 'system_table_skill.tbl.json'), encoding='utf-8'))
skill_status = json.load(open(os.path.join(BASE, 'system_table_skill_status.tbl.json'), encoding='utf-8'))

# sigil legal info from gem.tbl
sigil_info = {}
for g in gems:
    key = g['Key']
    name = sigils.get(key, {}).get('en') or sigils.get(key, {}).get('id') or f'0x{key:08X}'
    sigil_info[key] = {
        'name': name,
        'cn': sigils.get(key, {}).get('cn', ''),
        'primary': g['SkillId1'],
        'secondary': g['SkillId2'],   # 0x887AE0B0 = none
        'rarity': g['Rarity'],
    }

# 部分 V+ 因子(如 万能药＋/霸体＋/自动药水＋)在 gem.tbl 的 SkillId1 是无功能占位技能
# SKILL_023_00 (0xCAC6AFF2),真正的同名主词条在无 + 版因子上。这里把占位主词条修正为同名无 + 版的主词条。
DUMMY_SKILL_HASH = 0xCAC6AFF2
def _strip_plus(name):
    if name.endswith('＋'):
        return name[:-1]
    if name.endswith('+'):
        return name[:-1]
    return name

for key, info in sigil_info.items():
    if info['primary'] == DUMMY_SKILL_HASH:
        base_name = _strip_plus(info['name'])
        if base_name and base_name != info['name']:
            for k2, e2 in sigil_info.items():
                if k2 != key and e2['name'] == base_name and e2['primary'] != DUMMY_SKILL_HASH:
                    info['primary'] = e2['primary']
                    break

# trait max level from skill_status
trait_max = {}
for st in skill_status:
    h = st['Key']
    lv = st['Level']
    if h not in trait_max or lv > trait_max[h]:
        trait_max[h] = lv

# trait info: max level + name
trait_info = {}
for h, mx in trait_max.items():
    trait_info[h] = {
        'name': traits.get(h, {}).get('en') or traits.get(h, {}).get('id') or f'0x{h:08X}',
        'cn': traits.get(h, {}).get('cn', ''),
        'max_level': mx,
    }

extra = {'sigil_info': sigil_info, 'trait_info': trait_info, 'trait_max': trait_max}
with open(os.path.join(BASE, 'catalog_gem.json'), 'w', encoding='utf-8') as f:
    json.dump(extra, f, ensure_ascii=False, indent=1)
print(f'sigil_info={len(sigil_info)} trait_info={len(trait_info)} -> catalog_gem.json')

# ---- characters ----
chars = {}
for n in range(0, 3000, 100):
    gid = f'PL{n}'
    h = gbfr_hash(gid)
    chars[h] = gid
with open(os.path.join(BASE, 'catalog_chars.json'), 'w', encoding='utf-8') as f:
    json.dump(chars, f)
print(f'chars={len(chars)} -> catalog_chars.json')
