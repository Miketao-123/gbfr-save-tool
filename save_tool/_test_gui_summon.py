# -*- coding: utf-8 -*-
"""Headless test of the GUI summon tab logic (no window shown, drives methods directly)."""
import os, sys, io, shutil, tempfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
import gbfr_gui
import gbfr_cheat_tool as gct

# copy save to temp so we never touch the real one
src = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames', 'SaveData1.dat')
tmp = os.path.join(tempfile.gettempdir(), 'gbfr_gui_test_save.dat')
shutil.copy2(src, tmp)

root = tk.Tk()
root.withdraw()
app = gbfr_gui.App(root)
app.save_path.set(tmp)
app._force_reopen()
save = app._open()
assert save is not None, 'open failed'

# 1) refresh + list
app._sum_refresh(save)
app._summons_list(save)
out = app.summons_out.get('1.0', 'end')
assert '召唤石背包' in out and '路西法' in out or '★' in out, 'summon list output unexpected: %r' % out[:300]
print('[1] list OK, lines=%d' % len(out.strip().splitlines()))

# 2) load a record (first occupied slot)
rec = app._sum_records[0]
app.var_sum_slot.set(str(rec['slot']))
app.cmd_summons_load()
assert app._sum_cur is not None and app._sum_cur['slot'] == rec['slot'], 'load failed'
assert gct.summon_type_name(app._sum_cur['type_hash']) == app.var_sum_type.get().split(' [')[0], 'type name mismatch'
print('[2] load OK: slot=%d %s' % (rec['slot'], app.var_sum_type.get()[:40]))

# 3) type change updates natural pool in main combobox
th = app._sum_cur['type_hash']
app._sum_type_changed()
vals = list(app._sum_main_cb['values'])
te = gct.SUMCAT_TYPES.get(gct._sum_key(th), {})
pool = te.get('mainTraitHashes', [])
if pool:
    first_nat = '%s [0x%08X]' % (gct.summon_trait_name(pool[0]), int(pool[0]) & 0xFFFFFFFF)
    assert first_nat in vals, 'natural pool not in combo values'
print('[3] natural pool combos OK (%d pool traits)' % len(pool))

# 4) add preview (dry) via GUI
app.var_sum_type.set(gct.summon_type_name(th))
app.var_sum_main.set(gct.summon_trait_name(app._sum_cur['main_hash']))
app.var_sum_sub.set(gct.summon_sub_name(app._sum_cur['sub_hash']))
app.var_sum_mlv.set(str(app._sum_cur['main_level']))
app.var_sum_slv.set(str(app._sum_cur['sub_level']))
app.var_sum_rank.set(str(app._sum_cur['rank']))
n_before = len(app._sum_records)
app.cmd_summons_add(dry=True)
assert len(app._sum_records) == n_before, 'dry-run must not change inventory'
print('[4] add dry-run OK')

# 5) equip combos populated
assert app.var_sum_eq[0].get() != '' and '(空)' in app._sum_eq_cbs[0]['values'], 'equip combos not populated'
print('[5] equip combos OK: %d options' % len(app._sum_eq_cbs[0]['values']))

# 6) cleanup: no file writes happened (dry only) except copies
print('ALL GUI LOGIC TESTS PASSED')
root.destroy()
os.remove(tmp)
