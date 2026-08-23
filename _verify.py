# -*- coding: utf-8 -*-
"""校验 gbfr_gui.py 中业务方法是否与原文件逐字一致(视觉方法除外)。"""
import re
import sys

BUSINESS = [
    '_chara_choices', '_default_chara', '_open', '_vm', '_invalidate', '_force_reopen',
    '_items_rows', 'cmd_items_list', '_items_list', 'cmd_items_set',
    '_sigils_rows', 'cmd_sigils_list', '_sigils_list', '_resolve_secondary',
    '_sigils_add_common', 'cmd_sigils_add', 'cmd_sigils_add_dry',
    'cmd_chars_list', '_chars_list', 'cmd_chars_sigils', 'cmd_chars_clear',
    'cmd_summons_list', '_summons_list', 'cmd_summons_set',
    'cmd_ld_list', '_ld_list', 'cmd_ld_save', 'cmd_ld_restore',
    'cmd_om_list', 'cmd_om_set', 'cmd_om_clear', 'cmd_om_clear_all',
    'cmd_crab_run', 'cmd_wr_refresh', '_wr_resolve_trait', 'cmd_wr_add',
    'backup_save', '_note', '_set_text',
]
VISUAL = [
    '_build_top', '_build_notebook', '_mk_out', '_chara_cb',
    '_tab_items', '_tab_sigils', '_tab_chars', '_tab_summons', '_tab_loadout',
    '_build_log', '_tab_overmastery', '_tab_crab', '_tab_wrightstone',
    '_build_statusbar', '_show_about', '_on_close',
]


def extract(path, names):
    src = open(path, encoding='utf-8').read().split('\n')
    out = {}
    i = 0
    while i < len(src):
        m = re.match(r'^(?:    )?(?:@staticmethod\n)?def (\w+)\(', src[i])
        if m and m.group(1) in names:
            name = m.group(1)
            block = [src[i]]
            i += 1
            while i < len(src):
                if re.match(r'^(?:    )?def \w+\(', src[i]) or re.match(r'^class \w+', src[i]):
                    break
                block.append(src[i])
                i += 1
            out[name] = block
        else:
            i += 1
    return out


def main():
    old = extract('save_tool/gbfr_gui.py.orig', BUSINESS + VISUAL)
    new = extract('save_tool/gbfr_gui.py', BUSINESS + VISUAL)
    ok = True
    for name in BUSINESS:
        if name not in old:
            print('MISSING in orig:', name); ok = False; continue
        if name not in new:
            print('MISSING in new:', name); ok = False; continue
        o = [l.rstrip() for l in old[name]]
        n = [l.rstrip() for l in new[name]]
        if o != n:
            print('DIFF in business method:', name)
            ok = False
    for name in VISUAL:
        if name not in new:
            print('MISSING visual in new:', name); ok = False
        elif new[name][0].strip().endswith('raise NotImplementedError') or \
             any('raise NotImplementedError' in l for l in new[name]):
            print('STUB NOT REPLACED:', name); ok = False
    print('BUSINESS VERBATIM OK' if ok else 'CHECK FAILED')


if __name__ == '__main__':
    main()
