# -*- coding: utf-8 -*-
"""Compare skill/sub-param catalogs from all sources; check trait_info overlap."""
import sys, os, io, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def load(p):
    return json.load(open(p, encoding='utf-8'))

# sources
exe_skills = load('_patch_summon_skills.json')['skills']          # 1.8.5 exe
exe_subs = load('_patch_summon_subParams.json')['subParams']      # 1.8.5 exe
fe_skills = load(r'C:\Users\MikeT\AppData\Local\Temp\pet\data__summon_skills.json')['skills']  # master frontend
fe_subs = load(r'C:\Users\MikeT\AppData\Local\Temp\pet\data__summon_sub_params.json')['subParams']
be_skills = load(r'C:\Users\MikeT\AppData\Local\Temp\pet202\summon_skills.json')['skills']     # master backend
be_subs = load(r'C:\Users\MikeT\AppData\Local\Temp\pet202\summon_sub_params.json')['subParams']
fe_summons = load(r'C:\Users\MikeT\AppData\Local\Temp\pet\data__summons.json')['summons']      # master frontend types w/ EN

print('skills: exe=%d frontend=%d backend=%d' % (len(exe_skills), len(fe_skills), len(be_skills)))
print('subs: exe=%d frontend=%d backend=%d' % (len(exe_subs), len(fe_subs), len(be_subs)))
print('frontend summons with EN:', sum(1 for x in fe_summons if x.get('displayNameEn')))

# union of skill hashes
def hset(items):
    return {int(x['hash'], 16) & 0xFFFFFFFF for x in items}
u_skills = hset(exe_skills) | hset(fe_skills) | hset(be_skills)
u_subs = hset(exe_subs) | hset(fe_subs) | hset(be_subs)
print('union skills:', len(u_skills), 'union subs:', len(u_subs))

# overlap with gem trait_info
gem = load('catalog_gem.json')
ti = gem.get('trait_info', {})
ti_keys = {int(k) & 0xFFFFFFFF for k in ti}
print('trait_info hashes:', len(ti_keys))
print('skill overlap with trait_info:', len(u_skills & ti_keys))
print('sub overlap with trait_info:', len(u_subs & ti_keys))

# sample EN names from trait_info for a few skills
for h in list(u_skills & ti_keys)[:8]:
    e = ti[str(h)]
    print('  0x%08X' % h, e.get('cn'), '|', e.get('name'), 'max', e.get('max_level'))

# check sub params' display name style
print()
print('sub params sample:')
for s in exe_subs[:6]:
    print('  ', s['hash'], s['displayName'], 'max', s.get('maxLevel'), 'isPercent', s.get('isPercent'), 'values[:5]', s.get('values', [])[:5])
