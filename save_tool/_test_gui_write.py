# -*- coding: utf-8 -*-
"""GUI write-path test: set + equip on a temp copy of the save."""
import os, sys, io, shutil, tempfile
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
import gbfr_gui
import gbfr_cheat_tool as gct

src = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames', 'SaveData1.dat')
tmp = os.path.join(tempfile.gettempdir(), 'gbfr_gui_write_test.dat')
shutil.copy2(src, tmp)

root = tk.Tk()
root.withdraw()
app = gbfr_gui.App(root)
app.save_path.set(tmp)
app._force_reopen()
save = app._open()

# pick first record, bump rank
app._sum_refresh(save)
rec = app._sum_records[0]
app.var_sum_slot.set(str(rec['slot']))
app.cmd_summons_load()
new_rank = (rec['rank'] + 1) % 4
app.var_sum_rank.set(str(new_rank))
app.cmd_summons_set()
# verify
app._sum_refresh(save)
r2 = next((r for r in app._sum_records if r['slot'] == rec['slot']), None)
assert r2 is not None and r2['rank'] == new_rank, f'rank not updated: {r2}'
print('[set] rank {0} -> {1} OK (slot {2})'.format(rec['rank'], new_rank, rec['slot']))

# equip slot 1 -> this record (via equip combobox)
target = '槽%d · %s' % (rec['slot'], gct.summon_type_name(rec['type_hash']))
app.var_sum_eq[0].set(target)
app.cmd_summons_equip()
app._sum_refresh(save)
eq = app._sum_equipped
assert eq[0] == rec['slot'], f'equip slot1 not set: {eq}'
print('[equip] slot1 = %s OK' % target)

# unequip all
app.cmd_summons_unequip_all()
app._sum_refresh(save)
assert all(v == 0 for v in app._sum_equipped), 'unequip all failed'
print('[unequip] all cleared OK')

# hash integrity
s2 = gct.GBFRSaveData.open(tmp)
assert s2.check_active_hash() is not False, 'active hash invalid after writes'
print('[hash] checksum OK')
print('GUI WRITE TESTS PASSED')
root.destroy()
os.remove(tmp)
