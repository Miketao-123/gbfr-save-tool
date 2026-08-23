# -*- coding: utf-8 -*-
"""GBFR 存档修改器 - 图形界面(GUI)入口
基于 gbfr_cheat_tool.py 的本地存档修改功能,提供 tkinter 界面。
用法: python gbfr_gui.py  (或打包后的 GBFR存档修改器.exe)
"""
import os
import sys
import io
import json
import contextlib

# 让控制台输出 UTF-8(仅在源码模式有控制台时)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gbfr_cheat_tool as gct  # noqa: E402

import tkinter as tk
from tkinter import ttk, filedialog

APP_TITLE = "GBFR 存档修改器 v1.1"


def _chara_choices():
    """角色下拉框选项: '卡塔莉娜 (PL0200)' 形式;无名字的槽位显示 PL 代码。"""
    out = []
    for h, gid in sorted(gct.CHARSCAT.items(), key=lambda kv: kv[1]):
        if gid == 'PL000B':  # 非真实角色(dummy/LookDev)
            continue
        e = gct.CHAR_NAMES.get(gid)
        if e:
            cn = e.get('cn') or e.get('en') or gid
            out.append('%s (%s)' % (cn, gid))
        else:
            out.append(gid)
    return out


def _default_chara():
    """默认选中第一个有名字的角色(PL0000 古兰)。"""
    ch = _chara_choices()
    return ch[0] if ch else 'PL0000'


# ---------------------------------------------------------------- 日志捕获
class LogCapture(io.StringIO):
    """把 print 输出重定向到 GUI 日志框。"""
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def write(self, s):
        if s:
            self.widget.configure(state="normal")
            self.widget.insert("end", s)
            self.widget.see("end")
            self.widget.configure(state="disabled")
        return len(s)

    def flush(self):
        pass


# ---------------------------------------------------------------- 主窗口
class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1000x700")
        root.minsize(880, 620)

        self.save_path = tk.StringVar(value=gct.DEFAULT_SAVE)
        self.var_item_q = tk.StringVar()
        self.var_item_list = tk.StringVar()
        self.var_sigil_q = tk.StringVar()
        self.var_sigil_name = tk.StringVar()
        self.var_sigil_level = tk.StringVar()
        self.var_sigil_secondary = tk.StringVar()
        self.var_sigil_equip = tk.StringVar()
        self.var_chara = tk.StringVar()
        self.var_summon_unit = tk.StringVar()
        self.var_summon_chara = tk.StringVar()
        self.var_summon_level = tk.StringVar()
        self.var_ld_name = tk.StringVar()
        self.var_ld_chara = tk.StringVar()
        self.var_force = tk.BooleanVar(value=False)

        # 上限突破页
        self.var_om_chara = tk.StringVar(value=_default_chara())
        self.var_om_lane = tk.StringVar(value='0')
        self.var_om_effect = tk.StringVar(value='攻击力')
        self.var_om_value = tk.StringVar(value='1023')
        # 小钳蟹页
        self.var_crab_wee = tk.StringVar(value='20')
        self.var_crab_dark = tk.StringVar(value='20')
        self.var_crab_statue = tk.BooleanVar(value=True)
        self.var_crab_quest = tk.BooleanVar(value=True)
        # 武器祝福页
        self.var_wr_type = tk.StringVar(value=gct.WRIGHT_TYPES[0][0])
        self.var_wr_traits = [tk.StringVar() for _ in range(3)]
        self.var_wr_levels = [tk.StringVar(value=str(lv)) for lv in (20, 15, 10)]

        # 性能缓存:打开的存档 + 各 id_type 的 vm 字典(打开后记录不变,写档后失效)
        self._save = None
        self._save_path = None
        self._vm_cache = {}
        self._busy = False

        self._build_top()
        self._build_notebook()
        self._build_log()

        # 打开默认存档并刷新
        self.root.after(50, self.refresh_all)

    # ------------------------------------------------------------ 顶部
    def _build_top(self):
        f = ttk.Frame(self.root, padding=(8, 6))
        f.pack(fill="x")
        ttk.Label(f, text="存档路径:").pack(side="left")
        ttk.Entry(f, textvariable=self.save_path, width=58).pack(side="left", padx=4)
        ttk.Button(f, text="浏览…", command=self._pick_save).pack(side="left", padx=2)
        ttk.Button(f, text="打开并刷新", command=self.refresh_all).pack(side="left", padx=6)
        ttk.Button(f, text="备份当前存档", command=self.backup_save).pack(side="left", padx=2)
        ttk.Checkbutton(f, text="强制写入(游戏运行中,有风险)",
                        variable=self.var_force).pack(side="right", padx=4)

    def _pick_save(self):
        p = filedialog.askopenfilename(title="选择 SaveData1.dat",
                                       filetypes=[("存档文件", "*.dat"), ("所有文件", "*.*")])
        if p:
            self.save_path.set(p)
            self._force_reopen()
            self.refresh_all()

    # ------------------------------------------------------------ 选项卡
    def _build_notebook(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True, padx=8, pady=(4, 0))
        self._tab_items(nb)
        self._tab_sigils(nb)
        self._tab_chars(nb)
        self._tab_summons(nb)
        self._tab_loadout(nb)
        self._tab_overmastery(nb)
        self._tab_crab(nb)
        self._tab_wrightstone(nb)
        self.nb = nb

    def _mk_out(self, parent, height):
        t = tk.Text(parent, height=height, state="disabled", wrap="none",
                    bg="#101418", fg="#e8e8e8", insertbackground="white")
        t.pack(fill="both", expand=True, pady=(6, 0))
        sb = ttk.Scrollbar(t, command=t.yview)
        t.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        return t

    def _chara_cb(self, parent, var, width=16):
        """角色下拉框:可直接选择名字,也可手动输入 PL 代码/0x 哈希。"""
        cb = ttk.Combobox(parent, textvariable=var, width=width, state="normal",
                          values=_chara_choices())
        return cb

    def _tab_items(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 物品 ")
        top = ttk.Frame(t); top.pack(fill="x")
        ttk.Label(top, text="搜索:").pack(side="left")
        ttk.Entry(top, textvariable=self.var_item_q, width=22).pack(side="left", padx=4)
        ttk.Button(top, text="列出", command=self.cmd_items_list).pack(side="left", padx=2)
        ttk.Label(top, text="修改(名称 数量):").pack(side="left", padx=(16, 0))
        ttk.Entry(top, textvariable=self.var_item_list, width=26).pack(side="left", padx=4)
        ttk.Button(top, text="设置数量", command=self.cmd_items_set).pack(side="left", padx=2)
        self.items_out = self._mk_out(t, 15)

    def _tab_sigils(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 因子 ")
        top = ttk.Frame(t); top.pack(fill="x")
        ttk.Label(top, text="搜索:").pack(side="left")
        ttk.Entry(top, textvariable=self.var_sigil_q, width=22).pack(side="left", padx=4)
        ttk.Button(top, text="列出", command=self.cmd_sigils_list).pack(side="left", padx=2)

        mid = ttk.LabelFrame(t, text="生成合法因子", padding=8)
        mid.pack(fill="x", pady=6)
        g = ttk.Frame(mid); g.pack(fill="x")
        ttk.Label(g, text="因子(名称/0x):").pack(side="left")
        ttk.Entry(g, textvariable=self.var_sigil_name, width=26).pack(side="left", padx=4)
        ttk.Label(g, text="等级:").pack(side="left", padx=(8, 0))
        ttk.Entry(g, textvariable=self.var_sigil_level, width=5).pack(side="left", padx=4)
        ttk.Label(g, text="副词条:").pack(side="left", padx=(8, 0))
        ttk.Entry(g, textvariable=self.var_sigil_secondary, width=16).pack(side="left", padx=4)
        ttk.Label(g, text="装备给:").pack(side="left", padx=(8, 0))
        self._chara_cb(g, self.var_sigil_equip, width=16).pack(side="left", padx=4)
        b = ttk.Frame(mid); b.pack(fill="x", pady=(6, 0))
        ttk.Button(b, text="生成(写入存档)", command=self.cmd_sigils_add).pack(side="left", padx=2)
        ttk.Button(b, text="预览(不写入)", command=self.cmd_sigils_add_dry).pack(side="left", padx=2)
        self.sigils_out = self._mk_out(t, 10)

    def _tab_chars(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 角色 ")
        top = ttk.Frame(t); top.pack(fill="x")
        ttk.Label(top, text="角色:").pack(side="left")
        self._chara_cb(top, self.var_chara, width=16).pack(side="left", padx=4)
        ttk.Button(top, text="列出装备", command=self.cmd_chars_list).pack(side="left", padx=2)
        ttk.Button(top, text="查看该角色因子", command=self.cmd_chars_sigils).pack(side="left", padx=2)
        ttk.Button(top, text="卸下全部", command=self.cmd_chars_clear).pack(side="left", padx=2)
        self.chars_out = self._mk_out(t, 16)

    def _tab_summons(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 召唤石 ")
        top = ttk.Frame(t); top.pack(fill="x")
        ttk.Button(top, text="列出召唤石", command=self.cmd_summons_list).pack(side="left", padx=2)
        ttk.Label(top, text="槽号:").pack(side="left", padx=(16, 0))
        ttk.Entry(top, textvariable=self.var_summon_unit, width=7).pack(side="left", padx=4)
        ttk.Label(top, text="装备给:").pack(side="left", padx=(8, 0))
        self._chara_cb(top, self.var_summon_chara, width=16).pack(side="left", padx=4)
        ttk.Label(top, text="等级:").pack(side="left", padx=(8, 0))
        ttk.Entry(top, textvariable=self.var_summon_level, width=5).pack(side="left", padx=4)
        ttk.Button(top, text="更新", command=self.cmd_summons_set).pack(side="left", padx=4)
        self.summons_out = self._mk_out(t, 16)

    def _tab_loadout(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 配装方案 ")
        top = ttk.Frame(t); top.pack(fill="x")
        ttk.Button(top, text="列出方案", command=self.cmd_ld_list).pack(side="left", padx=2)
        ttk.Label(top, text="方案名:").pack(side="left", padx=(16, 0))
        ttk.Entry(top, textvariable=self.var_ld_name, width=14).pack(side="left", padx=4)
        ttk.Label(top, text="角色:").pack(side="left", padx=(8, 0))
        self._chara_cb(top, self.var_ld_chara, width=16).pack(side="left", padx=4)
        ttk.Button(top, text="保存方案", command=self.cmd_ld_save).pack(side="left", padx=2)
        ttk.Button(top, text="恢复方案", command=self.cmd_ld_restore).pack(side="left", padx=2)
        self.ld_out = self._mk_out(t, 16)

    # ------------------------------------------------------------ 日志
    def _build_log(self):
        f = ttk.LabelFrame(self.root, text="日志", padding=(6, 3))
        f.pack(fill="x", padx=8, pady=6)
        self.log = tk.Text(f, height=9, state="disabled", wrap="none", bg="#101418", fg="#e8e8e8")
        self.log.pack(fill="x")
        sb = ttk.Scrollbar(self.log, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self._capture = LogCapture(self.log)

    def _note(self, s):
        self._capture.write(s + "\n")

    def _open(self):
        """带缓存的存档打开:路径不变则复用已打开的存档对象(避免每次 2.3s 重开)。"""
        p = self.save_path.get().strip()
        if not os.path.isfile(p):
            self._note(f'[错误] 找不到存档: {p}')
            return None
        if self._save is not None and self._save_path == p:
            return self._save
        try:
            self._save = gct.GBFRSaveData.open(p)
            self._save_path = p
            self._vm_cache = {}
            return self._save
        except Exception as e:
            self._note(f'[错误] 打开存档失败: {e}')
            self._save = None
            self._save_path = None
            return None

    def _vm(self, idt):
        """带缓存的 vm:同一存档打开期间记录不变,直接复用。"""
        if idt not in self._vm_cache:
            self._vm_cache[idt] = gct.vm(self._save, idt)
        return self._vm_cache[idt]

    def _invalidate(self):
        """写档后清 vm 缓存(save 对象仍是最新状态,继续复用;下次读档重新取字典)。"""
        self._vm_cache = {}

    def _force_reopen(self):
        """强制重新打开存档(路径变化/用户点刷新时)。"""
        self._save = None
        self._save_path = None
        self._vm_cache = {}

    # ------------------------------------------------------------ 刷新
    def refresh_all(self):
        self._force_reopen()  # 手动刷新 = 重新读盘(外部改动/存档被替换)
        save = self._open()
        if save is None:
            return
        self._items_list(save)
        self._sigils_list(save)
        self._chars_list(save)
        self._summons_list(save)
        self._ld_list()
        self._note('--- 已刷新 ---')

    def backup_save(self):
        import shutil, time
        p = self.save_path.get().strip()
        if not os.path.isfile(p):
            self._note(f'[错误] 找不到存档: {p}')
            return
        bak = f'{p}.manual_{time.strftime("%Y%m%d_%H%M%S")}'
        shutil.copy2(p, bak)
        self._note(f'[完成] 已备份: {os.path.basename(bak)}')

    # ------------------------------------------------------------ 物品
    def _items_rows(self, save):
        m1801 = self._vm(gct.ID_ITEM_ID)
        m1802 = self._vm(gct.ID_ITEM_COUNT)
        q = self.var_item_q.get().strip().lower()
        rows = []
        for u, h in m1801.items():
            e = gct.CAT['items'].get(h) or gct.CAT['items'].get(str(h))
            name = (e['cn'] or e['en'] or e['id']) if e else f'0x{h:08X}'
            if q and q not in name.lower() and q not in f'0x{h:08X}'.lower():
                continue
            rows.append((u, name, m1802.get(u, 0)))
        rows.sort(key=lambda r: r[0])
        return rows

    def cmd_items_list(self):
        save = self._open()
        if save is None:
            return
        self._items_list(save)

    def _items_list(self, save):
        self._set_text(self.items_out, '')
        rows = self._items_rows(save)
        out = '\n'.join(f'  {name:<26} x{c:<6} (槽{u})' for u, name, c in rows)
        self._set_text(self.items_out, out if out else '(无匹配物品)')
        self._note(f'[信息] 物品 {len(rows)} 条')

    def cmd_items_set(self):
        q = self.var_item_list.get().strip()
        parts = q.rsplit(' ', 1)
        if len(parts) != 2 or not parts[1].lstrip('-').isdigit():
            self._note('[错误] 数量格式: "物品名 数量" 或 "物品名 x数量"')
            return
        name, cnt = parts[0], int(parts[1].lstrip('x'))
        save = self._open()
        if save is None:
            return
        e = gct.find_item(name)
        if e is None:
            self._note(f'[错误] 找不到物品: {name}'); return
        h = int(e.get('hash', '0'), 16) if 'hash' in e else next((hh for hh, x in gct.CAT['items'].items() if x is e), None)
        h = int(h)
        m1801 = self._vm(gct.ID_ITEM_ID)
        slot = next((u for u, v in m1801.items() if (v & 0xFFFFFFFF) == (h & 0xFFFFFFFF)), None)
        if slot is None:
            self._note(f'[错误] 该物品不在存档中(需先拥有): {e.get("id")}'); return
        rec = save.find_first('int', gct.ID_ITEM_COUNT, slot)
        old = save.get_first_value(rec)
        save.set_first_value(rec, cnt)
        bak = gct.save_and_backup(save, self.save_path.get(), 'item', force=self.var_force.get())
        self._invalidate()
        self._note(f'[完成] {e.get("cn") or e.get("en") or e.get("id")}: {old} -> {cnt} (槽{slot}) 备份:{os.path.basename(bak)}')
        self._items_list(save)

    # ------------------------------------------------------------ 因子
    def _sigils_rows(self, save):
        q = self.var_sigil_q.get().strip().lower()
        lines = []
        for hk, e in sorted(gct.GEMCAT['sigil_info'].items()):
            h = int(hk) & 0xFFFFFFFF
            name = e.get('cn') or e.get('name')
            if q and q not in name.lower() and q not in e.get('name', '').lower() and q not in f'0x{h:08X}'.lower():
                continue
            t2 = e.get('secondary')
            sec = ('+' if t2 and (t2 & 0xFFFFFFFF) != gct.EMPTY else '')
            lines.append(f'  {name:<28} {e.get("name",""):<26} 0x{h:08X} {sec}')
        return lines

    def cmd_sigils_list(self):
        save = self._open()
        if save is None:
            return
        self._sigils_list(save)

    def _sigils_list(self, save):
        self._set_text(self.sigils_out, '')
        lines = self._sigils_rows(save)
        self._set_text(self.sigils_out, '\n'.join(lines) if lines else '(无匹配因子)')
        self._note(f'[信息] 因子目录 {len(lines)} 条')

    def _resolve_secondary(self, info, e, gem_hash, sec):
        """返回 (trait2_hash, None) 或 (None, 错误消息)。"""
        fixed_sec = info['secondary']
        if not sec:
            return fixed_sec, None
        t2 = gct.find_trait(sec)
        if t2 is None:
            return None, f'找不到词条: {sec}'
        t2h = next((int(hk) for hk, x in gct.GEMCAT['trait_info'].items() if x is t2), None)
        allowed = gct.legal_secondary_ids(gem_hash)
        if gct._can_mix(gem_hash):
            if t2h not in allowed:
                return None, f'词条「{t2.get("name")}」不是因子「{e.get("cn") or e.get("name")}」的合法副词条'
        elif fixed_sec in (gct.EMPTY, None):
            if t2h not in allowed:
                return None, f'词条「{t2.get("name")}」不是因子「{e.get("cn") or e.get("name")}」的合法副词条'
        elif t2h != fixed_sec:
            return None, f'该因子副词条固定为 0x{fixed_sec:08X},不能自定义'
        return t2h, None

    def _sigils_add_common(self, dry):
        name = self.var_sigil_name.get().strip()
        if not name:
            self._note('[错误] 请输入因子名称或 0x哈希'); return
        save = self._open()
        if save is None:
            return
        e = gct.find_sigil(name)
        if e is None:
            self._note(f'[错误] 找不到因子: {name}'); return
        gem_hash = next((int(hk) for hk, x in gct.GEMCAT['sigil_info'].items() if x is e), None)
        info = gct.GEMCAT['sigil_info'][str(gem_hash)]
        primary = info['primary']
        mx = gct.GEMCAT['trait_info'].get(str(primary), {}).get('max_level', 20)
        lv = self.var_sigil_level.get().strip()
        level = int(lv) if lv and lv.lstrip('-').isdigit() else mx
        if level > mx:
            self._note(f'[警告] 等级 {level} 超过主词条上限 {mx},已截断')
            level = mx
        trait2, err = self._resolve_secondary(info, e, gem_hash, self.var_sigil_secondary.get().strip() or None)
        if err:
            self._note(f'[错误] {err}'); return
        worn = None
        if self.var_sigil_equip.get().strip():
            ch, gid = gct.find_chara(self.var_sigil_equip.get().strip())
            if ch is None:
                self._note(f'[错误] 找不到角色: {self.var_sigil_equip.get().strip()}'); return
            err = gct.check_equip_limit(save, ch, gid)
            if err:
                self._note(f'[错误] {err}'); return
            worn = ch
        try:
            slot = gct.add_sigil_to_save(save, gem_hash, level, primary, trait2, worn, dry=dry)
        except RuntimeError as ex:
            self._note(f'[错误] {ex}'); return
        if dry:
            self._note(f'[预览] 槽{slot}: {e.get("cn") or e.get("name")} lv{level} 副词条=0x{trait2:08X} '
                       f'装备={gct.chara_label(gid) if worn else "无"}')
            return
        bak = gct.save_and_backup(save, self.save_path.get(), 'sigil', force=self.var_force.get())
        self._invalidate()
        self._note(f'[完成] 已生成 {e.get("cn") or e.get("name")} (槽{slot}, 等级{level}) 备份:{os.path.basename(bak)}')
        self._sigils_list(save)

    def cmd_sigils_add(self):
        self._sigils_add_common(dry=False)

    def cmd_sigils_add_dry(self):
        self._sigils_add_common(dry=True)

    # ------------------------------------------------------------ 角色
    def cmd_chars_list(self):
        save = self._open()
        if save is None:
            return
        self._chars_list(save)

    def _chars_list(self, save):
        self._set_text(self.chars_out, '')
        m2703 = self._vm(gct.ID_2703)
        m2706 = self._vm(gct.ID_2706)
        equips = {}
        for u, g in m2703.items():
            if (g & 0xFFFFFFFF) == gct.EMPTY:
                continue
            worn = m2706.get(u)
            if worn and worn != gct.EMPTY:
                equips.setdefault(worn, []).append(u)
        lines = []
        for h, gid in gct.CHARSCAT.items():
            n = len(equips.get(int(h) & 0xFFFFFFFF, []))
            if n:
                lines.append(f'  {gct.chara_label(gid)} [{gid}] (0x{int(h)&0xFFFFFFFF:08X}): {n} 个因子')
        self._set_text(self.chars_out, '\n'.join(lines) if lines else '(没有角色装备因子)')

    def cmd_chars_sigils(self):
        save = self._open()
        if save is None:
            return
        ch_hash, gid = gct.find_chara(self.var_chara.get().strip())
        if ch_hash is None:
            self._note(f'[错误] 找不到角色: {self.var_chara.get().strip()}'); return
        self._set_text(self.chars_out, '')
        m2703 = self._vm(gct.ID_2703); m2704 = self._vm(gct.ID_2704); m2706 = self._vm(gct.ID_2706)
        m1701 = self._vm(gct.ID_1701)
        mine = [u for u, g in m2703.items() if (g & 0xFFFFFFFF) != gct.EMPTY and m2706.get(u) == ch_hash]
        lines = [f'=== {gct.chara_label(gid)} 装备的因子 ===']
        for u in sorted(mine):
            idx = u - gct.GEM_SLOT_BASE
            g = m2703.get(u)
            e = gct.GEMCAT['sigil_info'].get(str(g))
            t1 = m1701.get(gct.TRAIT_REC_BASE + idx * 100)
            name = (e.get('cn') or e.get('name')) if e else f'0x{g:08X}'
            lines.append(f'  槽{u}: {name:<26} lv{m2704.get(u)}')
        self._set_text(self.chars_out, '\n'.join(lines) if len(lines) > 1 else f'{gct.chara_label(gid)} 未装备因子')

    def cmd_chars_clear(self):
        save = self._open()
        if save is None:
            return
        ch_hash, gid = gct.find_chara(self.var_chara.get().strip())
        if ch_hash is None:
            self._note(f'[错误] 找不到角色: {self.var_chara.get().strip()}'); return
        m2702 = self._vm(gct.ID_2702)
        m2703 = self._vm(gct.ID_2703); m2706 = self._vm(gct.ID_2706)
        changed = 0
        for u in [u for u, g in m2703.items() if (g & 0xFFFFFFFF) != gct.EMPTY and m2706.get(u) == ch_hash]:
            gct.set_first(save, gct.ID_2706, u, gct.EMPTY, 'uint')
            gct.sigil_equip_unregister(save, ch_hash, m2702.get(u, 0))
            changed += 1
        bak = gct.save_and_backup(save, self.save_path.get(), 'unequip', force=self.var_force.get())
        self._invalidate()
        self._note(f'[完成] 已卸下 {gct.chara_label(gid)} 的 {changed} 个因子 备份:{os.path.basename(bak)}')

    # ------------------------------------------------------------ 召唤石
    def cmd_summons_list(self):
        save = self._open()
        if save is None:
            return
        self._summons_list(save)

    def _summons_list(self, save):
        self._set_text(self.summons_out, '')
        m3101 = self._vm(3101); m3102 = self._vm(3102); m3113 = self._vm(3113)
        units = sorted(set(m3101) | set(m3102) | set(m3113))
        lines = ['=== 召唤石 ===']
        for u in units:
            worn = m3101.get(u)
            ch = gct.chara_label_by_hash(worn) if worn and worn != gct.EMPTY else '未装备'
            t = m3113.get(u)
            lines.append(f'  槽{u}: 装备={ch} 等级={m3102.get(u,0)} typeHash=0x{(t or 0):08X}')
        self._set_text(self.summons_out, '\n'.join(lines) if len(lines) > 1 else '(无召唤石)')

    def cmd_summons_set(self):
        save = self._open()
        if save is None:
            return
        u = self.var_summon_unit.get().strip()
        if not u or not u.lstrip('-').isdigit():
            self._note('[错误] 请输入召唤石槽号'); return
        u = int(u)
        ch = self.var_summon_chara.get().strip() or None
        lv = self.var_summon_level.get().strip()
        lv = int(lv) if lv and lv.lstrip('-').isdigit() else None
        if ch:
            ch_hash, gid = gct.find_chara(ch)
            if ch_hash is None:
                self._note(f'[错误] 找不到角色: {ch}'); return
            gct.set_first(save, gct.ID_SUM_CHARA, u, ch_hash, 'uint')
        if lv is not None:
            gct.set_first(save, gct.ID_SUM_LEVEL, u, lv, 'int')
        bak = gct.save_and_backup(save, self.save_path.get(), 'summon', force=self.var_force.get())
        self._invalidate()
        self._note(f'[完成] 召唤石槽{u} 已更新 备份:{os.path.basename(bak)}')
        self._summons_list(save)

    # ------------------------------------------------------------ 配装
    def cmd_ld_list(self):
        self._ld_list()

    def _ld_list(self):
        self._set_text(self.ld_out, '')
        ld_dir = gct.WRITE_DIR
        os.makedirs(ld_dir, exist_ok=True)
        names = [fn[:-5] for fn in sorted(os.listdir(ld_dir)) if fn.endswith('.json')]
        self._set_text(self.ld_out, '\n'.join(f'  {n}' for n in names) if names else '(暂无配装方案)')
        self._note(f'[信息] 配装方案目录: {ld_dir}')

    def cmd_ld_save(self):
        save = self._open()
        if save is None:
            return
        name = self.var_ld_name.get().strip()
        ch = self.var_ld_chara.get().strip()
        if not name or not ch:
            self._note('[错误] 请输入方案名和角色'); return
        ch_hash, gid = gct.find_chara(ch)
        if ch_hash is None:
            self._note(f'[错误] 找不到角色: {ch}'); return
        m2703 = self._vm(gct.ID_2703); m2704 = self._vm(gct.ID_2704); m2706 = self._vm(gct.ID_2706)
        mine = [u for u, g in m2703.items() if (g & 0xFFFFFFFF) != gct.EMPTY and m2706.get(u) == ch_hash]
        data = {'chara': gid, 'sigils': [{'slot': u, 'gem': m2703[u], 'level': m2704.get(u)} for u in sorted(mine)]}
        ld_dir = gct.WRITE_DIR
        os.makedirs(ld_dir, exist_ok=True)
        with open(os.path.join(ld_dir, name + '.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        self._note(f'[完成] 已保存 {gct.chara_label(gid)} 的 {len(data["sigils"])} 个因子配装 -> {name}.json')
        self._ld_list()

    def cmd_ld_restore(self):
        save = self._open()
        if save is None:
            return
        name = self.var_ld_name.get().strip()
        if not name:
            self._note('[错误] 请输入方案名'); return
        p = os.path.join(gct.WRITE_DIR, name + '.json')
        if not os.path.exists(p):
            self._note(f'[错误] 找不到配装: {name}'); return
        data = json.load(open(p, encoding='utf-8'))
        ch_hash, gid = gct.find_chara(data.get('chara', name))
        if ch_hash is None:
            self._note(f'[错误] 配装角色无法识别: {data.get("chara")}'); return
        m2702 = self._vm(gct.ID_2702)
        m2703 = self._vm(gct.ID_2703); m2704 = self._vm(gct.ID_2704); m2706 = self._vm(gct.ID_2706)
        m2707 = self._vm(gct.ID_2707)
        for u in [u for u, g in m2703.items() if (g & 0xFFFFFFFF) != gct.EMPTY and m2706.get(u) == ch_hash]:
            gct.set_first(save, gct.ID_2706, u, gct.EMPTY, 'uint')
            gct.sigil_equip_unregister(save, ch_hash, m2702.get(u, 0))
        ok = 0
        for s in data.get('sigils', []):
            u = s['slot']
            if u in m2703 and (m2703[u] & 0xFFFFFFFF) == s['gem']:
                gct.set_first(save, gct.ID_2706, u, ch_hash, 'uint')
                gct.set_first(save, gct.ID_2707, u, (m2707.get(u, 0) & ~3) | 2, 'uint')
                gct.sigil_equip_register(save, ch_hash, m2702.get(u, 0))
                ok += 1
        bak = gct.save_and_backup(save, self.save_path.get(), 'loadout', force=self.var_force.get())
        self._invalidate()
        self._note(f'[完成] 已恢复配装 {name} 到 {gct.chara_label(gid)} (装备 {ok}/{len(data.get("sigils",[]))}) 备份:{os.path.basename(bak)}')

    def _tab_overmastery(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 上限突破 ")
        top = ttk.Frame(t); top.pack(fill="x")
        ttk.Label(top, text="角色:").pack(side="left")
        self._chara_cb(top, self.var_om_chara, width=16).pack(side="left", padx=4)
        ttk.Button(top, text="读取该角色", command=self.cmd_om_list).pack(side="left", padx=2)
        ttk.Label(top, text="槽位(0-3):").pack(side="left", padx=(16, 0))
        ttk.Entry(top, textvariable=self.var_om_lane, width=4).pack(side="left", padx=4)
        ttk.Label(top, text="效果:").pack(side="left", padx=(8, 0))
        ttk.Combobox(top, textvariable=self.var_om_effect, width=16, state="normal",
                     values=list(gct.OM_EFFECTS.keys())).pack(side="left", padx=4)
        ttk.Label(top, text="数值:").pack(side="left", padx=(8, 0))
        ttk.Entry(top, textvariable=self.var_om_value, width=6).pack(side="left", padx=4)
        ttk.Button(top, text="写入该槽", command=self.cmd_om_set).pack(side="left", padx=2)
        ttk.Button(top, text="清空该槽", command=self.cmd_om_clear).pack(side="left", padx=2)
        ttk.Button(top, text="全部清空", command=self.cmd_om_clear_all).pack(side="left", padx=4)
        self.om_out = self._mk_out(t, 14)

    def _tab_crab(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 小钳蟹 ")
        top = ttk.Frame(t); top.pack(fill="x")
        ttk.Label(top, text="普通小钳蟹数量:").pack(side="left")
        ttk.Entry(top, textvariable=self.var_crab_wee, width=6).pack(side="left", padx=4)
        ttk.Label(top, text="漆黑小钳蟹数量:").pack(side="left", padx=(10, 0))
        ttk.Entry(top, textvariable=self.var_crab_dark, width=6).pack(side="left", padx=4)
        ttk.Checkbutton(top, text="漆黑蟹像=1", variable=self.var_crab_statue).pack(side="left", padx=(12, 2))
        ttk.Checkbutton(top, text="完成收集任务", variable=self.var_crab_quest).pack(side="left", padx=4)
        ttk.Button(top, text="执行小钳蟹修改", command=self.cmd_crab_run).pack(side="left", padx=8)
        self.crab_out = self._mk_out(t, 14)

    # ------------------------------------------------------------ 上限突破
    def cmd_om_list(self):
        save = self._open()
        if save is None:
            return
        ch = self.var_om_chara.get().strip()
        rows, err = gct.get_overmastery(save, ch)
        if err:
            self._note(f'[错误] {err}'); return
        _, _gid = gct.find_chara(ch)
        disp = gct.chara_label(_gid) if _gid else ch
        self._set_text(self.om_out, '')
        lines = [f'=== {disp} 上限突破 (Overmastery) ===',
                 '     (存档值 512=满档/10⭐, 1023=80% 改档上限)']
        for i, (name, val, h, dispv) in enumerate(rows):
            if name == '空':
                lines.append(f'  槽{i}: (空)')
            else:
                lines.append(f'  槽{i}: {name:<12} 显示={dispv:<11} 存档值={val}/1023  0x{h:08X}')
        self._set_text(self.om_out, '\n'.join(lines))

    def cmd_om_set(self):
        save = self._open()
        if save is None:
            return
        ch = self.var_om_chara.get().strip()
        lane = self.var_om_lane.get().strip()
        if not lane.lstrip('-').isdigit():
            self._note('[错误] 槽位必须是 0-3'); return
        lane = int(lane)
        val = self.var_om_value.get().strip()
        if not val.lstrip('-').isdigit():
            self._note('[错误] 数值必须是整数 0-1023'); return
        err = gct.set_overmastery(save, ch, lane, self.var_om_effect.get().strip(), int(val))
        if err:
            self._note(f'[错误] {err}'); return
        bak = gct.save_and_backup(save, self.save_path.get(), 'overmastery', force=self.var_force.get())
        self._invalidate()
        _, _gid = gct.find_chara(ch)
        disp = gct.chara_label(_gid) if _gid else ch
        self._note(f'[完成] {disp} 槽{lane} 已设置: {self.var_om_effect.get().strip()} = {val} 备份:{os.path.basename(bak)}')
        self.cmd_om_list()

    def cmd_om_clear(self):
        save = self._open()
        if save is None:
            return
        ch = self.var_om_chara.get().strip()
        lane = self.var_om_lane.get().strip()
        if not lane.lstrip('-').isdigit():
            self._note('[错误] 槽位必须是 0-3'); return
        err = gct.set_overmastery(save, ch, int(lane), '', 0)
        if err:
            self._note(f'[错误] {err}'); return
        bak = gct.save_and_backup(save, self.save_path.get(), 'overmastery', force=self.var_force.get())
        self._invalidate()
        _, _gid = gct.find_chara(ch)
        disp = gct.chara_label(_gid) if _gid else ch
        self._note(f'[完成] {disp} 槽{lane} 已清空 备份:{os.path.basename(bak)}')
        self.cmd_om_list()

    def cmd_om_clear_all(self):
        save = self._open()
        if save is None:
            return
        ch = self.var_om_chara.get().strip()
        for lane in range(4):
            gct.set_overmastery(save, ch, lane, '', 0)
        bak = gct.save_and_backup(save, self.save_path.get(), 'overmastery', force=self.var_force.get())
        self._invalidate()
        _, _gid = gct.find_chara(ch)
        disp = gct.chara_label(_gid) if _gid else ch
        self._note(f'[完成] {disp} 全部 4 槽上限突破已清空 备份:{os.path.basename(bak)}')
        self.cmd_om_list()

    # ------------------------------------------------------------ 小钳蟹
    def cmd_crab_run(self):
        save = self._open()
        if save is None:
            return
        try:
            wee = int(self.var_crab_wee.get().strip())
            dark = int(self.var_crab_dark.get().strip())
        except ValueError:
            self._note('[错误] 数量必须是整数'); return
        m1801 = self._vm(gct.ID_ITEM_ID)
        for label, h, cnt in (('普通小钳蟹', 0xEE2559C6, wee), ('漆黑小钳蟹', 0x9FBA96D1, dark)):
            slot = next((u for u, v in m1801.items() if (v & 0xFFFFFFFF) == (h & 0xFFFFFFFF)), None)
            if slot is None:
                self._note(f'[警告] 存档中未找到「{label}」(需先拥有该物品)')
                continue
            rec = save.find_first('int', gct.ID_ITEM_COUNT, slot)
            old = save.get_first_value(rec)
            save.set_first_value(rec, cnt)
            self._note(f'[物品] {label}: {old} -> {cnt} (槽{slot})')
        if self.var_crab_statue.get():
            h = 0x076A9F41
            slot = next((u for u, v in m1801.items() if (v & 0xFFFFFFFF) == h), None)
            if slot is not None:
                rec = save.find_first('int', gct.ID_ITEM_COUNT, slot)
                old = save.get_first_value(rec)
                save.set_first_value(rec, 1)
                self._note(f'[奖励] 漆黑蟹像: {old} -> 1 (槽{slot})')
            else:
                self._note('[警告] 存档中未找到「漆黑蟹像」')
        if self.var_crab_quest.get():
            hit, changed = gct.complete_crab_quests(save)
            self._note(f'[任务] 命中的蟹任务 {hit} 个,改动 {changed} 个标志')
        bak = gct.save_and_backup(save, self.save_path.get(), 'crab', force=self.var_force.get())
        self._invalidate()
        self._note(f'[完成] 小钳蟹功能已写入 备份:{os.path.basename(bak)}')

    # ------------------------------------------------------------ 武器祝福
    def _tab_wrightstone(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 祝福 ")
        top = ttk.Frame(t); top.pack(fill="x")
        ttk.Label(top, text="祝福类型:").pack(side="left")
        ttk.Combobox(top, textvariable=self.var_wr_type, width=20, state="readonly",
                     values=['%s (%s)' % (x[0], x[1]) for x in gct.WRIGHT_TYPES]).pack(side="left", padx=4)
        ttk.Button(top, text="刷新词条列表", command=self.cmd_wr_refresh).pack(side="left", padx=6)

        mid = ttk.LabelFrame(t, text="祝福配置(3 个词条 + 等级,等级 0-20)", padding=8)
        mid.pack(fill="x", pady=6)
        self._wr_trait_combos = []
        for i in range(3):
            row = ttk.Frame(mid); row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"词条{i+1}:").pack(side="left")
            cb = ttk.Combobox(row, textvariable=self.var_wr_traits[i], width=22, state="normal")
            cb.pack(side="left", padx=4)
            self._wr_trait_combos.append(cb)
            ttk.Label(row, text="等级:").pack(side="left", padx=(8, 0))
            ttk.Entry(row, textvariable=self.var_wr_levels[i], width=4).pack(side="left", padx=4)
        b = ttk.Frame(mid); b.pack(fill="x", pady=(6, 0))
        ttk.Button(b, text="生成祝福(写入存档)", command=lambda: self.cmd_wr_add(dry=False)).pack(side="left", padx=2)
        ttk.Button(b, text="预览(不写入)", command=lambda: self.cmd_wr_add(dry=True)).pack(side="left", padx=2)
        self.wr_out = self._mk_out(t, 12)

    def cmd_wr_refresh(self):
        save = self._open()
        if save is None:
            return
        pool = gct.wrightstone_trait_pool(save)
        vals = sorted('%s (%s)' % (cn, en) if en else cn for cn, en in pool.values())
        for i in range(3):
            # 刷新下拉框选项(保留当前值)
            w = self._wr_trait_combos[i]
            cur = self.var_wr_traits[i].get()
            w.configure(values=vals)
            if cur:
                self.var_wr_traits[i].set(cur)
        self._note(f'[信息] 祝福词条池 {len(vals)} 种')

    def _wr_resolve_trait(self, q):
        """词条名 -> 哈希;失败返回 None。"""
        q = (q or '').strip()
        if not q:
            return None
        if q.lower().startswith('0x'):
            return int(q, 16) & 0xFFFFFFFF
        t2 = gct.find_trait(q)
        if t2 is not None:
            return next((int(hk) for hk, x in gct.GEMCAT['trait_info'].items() if x is t2), None)
        return None

    def cmd_wr_add(self, dry=False):
        save = self._open()
        if save is None:
            return
        wt = gct.find_wrightstone_type(self.var_wr_type.get())
        if wt is None:
            self._note('[错误] 请选择祝福类型'); return
        traits = []
        for i in range(3):
            q = self.var_wr_traits[i].get().strip()
            if not q:
                continue
            th = self._wr_resolve_trait(q)
            if th is None:
                self._note(f'[错误] 找不到词条: {q}(可用"刷新词条列表"查看)'); return
            lv = self.var_wr_levels[i].get().strip()
            try:
                lv = int(lv) if lv else gct.WRIGHT_MAX_LEVEL
            except ValueError:
                self._note('[错误] 等级必须是 0-20 的整数'); return
            traits.append((th, lv))
        if not traits:
            traits = [(wt[3], gct.WRIGHT_MAX_LEVEL)]  # 默认词条
        try:
            slot = gct.add_wrightstone(save, wt[2], traits, dry=dry)
        except RuntimeError as ex:
            self._note(f'[错误] {ex}'); return
        if dry:
            self._note(f'[预览] 将生成 {wt[0]} (槽{slot}, 序列号=当前+1) '
                       f'词条: {"; ".join("%s lv%s" % (gct.GEMCAT["trait_info"].get(str(th), {}).get("cn") or "0x%08X" % th, lv) for th, lv in traits)}')
            return
        bak = gct.save_and_backup(save, self.save_path.get(), 'wrightstone', force=self.var_force.get())
        self._invalidate()
        m2103 = self._vm(gct.WRIGHT_SERIAL_FIELD)
        self._note(f'[完成] 已生成 {wt[0]} (槽{slot}, 序列号={m2103.get(slot)}) 备份:{os.path.basename(bak)}')

    # ------------------------------------------------------------ 工具
    @staticmethod
    def _set_text(w, s):
        w.configure(state="normal")
        w.delete("1.0", "end")
        w.insert("1.0", s)
        w.configure(state="disabled")


def main():
    root = tk.Tk()
    try:
        App(root)
    except Exception:
        root.destroy()
        raise
    root.mainloop()


if __name__ == '__main__':
    main()
