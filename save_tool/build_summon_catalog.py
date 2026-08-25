# -*- coding: utf-8 -*-
"""Build catalog_summon.json — merged summon catalog for the save editor.

Sources (all extracted from / matching the official GBFR PE Patch Tool):
  1. _patch_summon_summons.json   — 189 summon types, extracted from the user's
                                    PE Patch Tool 1.8.5 exe (CN display names)
  2. summon_natural_rules_202.json — DLC 2.0.2 summon.tbl natural rules
                                    (per-type main/sub pools + levels + tier/mode)
  3. data__summons.json (repo frontend) — same 189 types with EN names + code
  4. _patch_summon_skills.json     — 230 main traits (CN) from the 1.8.5 exe
  5. data__summon_skills.json      — master frontend main traits (CN)
  6. summon_skills.json (master backend) — main traits
  7. _patch_summon_subParams.json  — 22 sub params (CN) + value tables
  8. catalog_gem.json trait_info   — EN names for overlapping sigil traits

Output: catalog_summon.json with keys: types / main_traits / sub_params / meta
"""
import json, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

HERE = os.path.dirname(os.path.abspath(__file__))
PET = r'C:\Users\MikeT\AppData\Local\Temp\pet'
PET202 = r'C:\Users\MikeT\AppData\Local\Temp\pet202'

def load(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)

def norm(h):
    return int(h, 16) & 0xFFFFFFFF

# ---- 1. types ----
types = {}  # hash -> {cn, en, baseName, code, cost, typeName}
for e in load(os.path.join(HERE, '_patch_summon_summons.json'))['summons']:
    h = norm(e['hash'])
    types.setdefault(h, {}).update({
        'cn': e.get('displayName', ''),
        'baseName': e.get('baseName', ''),
        'code': e.get('code', ''),
        'cost': e.get('cost', 0),
        'typeName': e.get('typeName', ''),
    })
# EN names from repo frontend (master)
fe_summons = load(os.path.join(PET, 'data__summons.json'))['summons']
for e in fe_summons:
    h = norm(e['hash'])
    if h in types:
        types[h]['en'] = e.get('displayNameEn', '')
        for k in ('baseName', 'code', 'cost', 'typeName'):
            if not types[h].get(k) and e.get(k):
                types[h][k] = e[k]
    else:
        types[h] = {
            'cn': e.get('displayName', ''), 'en': e.get('displayNameEn', ''),
            'baseName': e.get('baseName', ''), 'code': e.get('code', ''),
            'cost': e.get('cost', 0), 'typeName': e.get('typeName', ''),
        }

# ---- 2. natural rules (2.0.2) ----
rules = load(os.path.join(PET202, 'summon_natural_rules_202.json'))['rows']
for r in rules:
    h = norm(r['typeHash'])
    if h not in types:
        types[h] = {'cn': r.get('name', ''), 'en': '', 'baseName': r.get('name', ''),
                    'code': '', 'cost': r.get('equipCost', 0), 'typeName': r.get('typeName', '')}
    types[h]['tier'] = r.get('tier', '')
    types[h]['tierIndex'] = r.get('tierIndex', 0)
    types[h]['variant'] = r.get('variant', 0)
    types[h]['mode'] = r.get('mode', '')
    types[h]['equipCost'] = r.get('equipCost', 0)
    types[h]['mainTraitHashes'] = [norm(x) for x in r.get('mainTraitHashes', [])]
    types[h]['subParamHashes'] = [norm(x) for x in r.get('subParamHashes', [])]
    types[h]['mainTraitLevels'] = r.get('mainTraitLevels', [])
    types[h]['subParamLevels'] = r.get('subParamLevels', [])

# ---- 3. main traits ----
main_traits = {}
def merge_main(e):
    h = norm(e['hash'])
    d = main_traits.setdefault(h, {})
    d['cn'] = e.get('displayName', '') or d.get('cn', '')
    if e.get('maxLevel') is not None:
        d['maxLevel'] = max(d.get('maxLevel', 0), int(e['maxLevel']))
for src in ('_patch_summon_skills.json',):
    for e in load(os.path.join(HERE, src))['skills']:
        merge_main(e)
for src in (os.path.join(PET, 'data__summon_skills.json'),
            os.path.join(PET202, 'summon_skills.json')):
    for e in load(src)['skills']:
        merge_main(e)

# ---- 4. sub params ----
sub_params = {}
for e in load(os.path.join(HERE, '_patch_summon_subParams.json'))['subParams']:
    h = norm(e['hash'])
    sub_params[h] = {
        'cn': e.get('displayName', ''), 'en': '',
        'maxLevel': e.get('maxLevel', 0),
        'isPercent': bool(e.get('isPercent', False)),
        'values': e.get('values', []),
    }
for e in load(os.path.join(PET, 'data__summon_sub_params.json'))['subParams']:
    h = norm(e['hash'])
    d = sub_params.setdefault(h, {'cn': '', 'en': '', 'maxLevel': 0, 'isPercent': False, 'values': []})
    if e.get('displayName') and not d['cn']:
        d['cn'] = e['displayName']
    if e.get('maxLevel') is not None:
        d['maxLevel'] = max(d['maxLevel'], int(e['maxLevel']))

# ---- 5. EN names for main traits from sigil trait_info ----
gem = load(os.path.join(HERE, 'catalog_gem.json'))
ti = gem.get('trait_info', {})
for hk, e in ti.items():
    h = int(hk) & 0xFFFFFFFF
    if h in main_traits:
        main_traits[h]['en'] = e.get('name', '') or main_traits[h].get('en', '')
        if not main_traits[h].get('cn'):
            main_traits[h]['cn'] = e.get('cn', '')

# ---- serialize ----
def to_str_keys(d):
    return {str(k): v for k, v in sorted(d.items())}

out = {
    'meta': {
        'format': 1,
        'types': len(types),
        'main_traits': len(main_traits),
        'sub_params': len(sub_params),
        'natural_rules_version': '2.0.2',
        'note': '来源: GBFR PE Patch Tool (summons.json/summon_skills.json/summon_sub_params.json/summon_natural_rules_202.json)',
    },
    'types': to_str_keys(types),
    'main_traits': to_str_keys(main_traits),
    'sub_params': to_str_keys(sub_params),
}
dst = os.path.join(HERE, 'catalog_summon.json')
with open(dst, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('written', dst)
print('types:', len(types), 'main_traits:', len(main_traits), 'sub_params:', len(sub_params))
# sanity: print counts of types with natural rules
n_rule = sum(1 for v in types.values() if v.get('mainTraitHashes'))
print('types with natural rules:', n_rule)
