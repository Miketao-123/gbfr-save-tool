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
import threading

# 让控制台输出 UTF-8(仅在源码模式有控制台时)
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gbfr_cheat_tool as gct  # noqa: E402

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import gui_theme as th  # 暗色主题模块(翻新新增)

APP_TITLE = "GBFR 存档修改器 v1.4"


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
    """把 print 输出重定向到 GUI 日志框(按行用主题模块自动着色)。"""
    def __init__(self, widget):
        super().__init__()
        self.widget = widget

    def write(self, s):
        if s:
            self.widget.configure(state="normal")
            for seg in s.split("\n"):
                if seg:
                    th.emit_line(self.widget, seg + "\n")
            self.widget.configure(state="disabled")
        return len(s)

    def flush(self):
        pass


# ---------------------------------------------------------------- 主窗口
class App:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.minsize(880, 620)

        # 暗色主题(必须在创建任何控件之前应用)
        th.apply_theme(root)

        # 恢复上次窗口几何
        try:
            with open(os.path.join(gct.WRITE_DIR, 'ui_state.json'), encoding='utf-8') as f:
                geo = json.load(f).get('geometry')
            if geo:
                root.geometry(geo)
        except Exception:
            root.geometry("1000x700")

        # 程序化绘制图标(失败不影响启动)
        try:
            self._icon = th.make_icon()
            root.iconphoto(True, self._icon)
        except Exception:
            pass

        self.save_path = tk.StringVar(value=gct.DEFAULT_SAVE)
        self.var_item_q = tk.StringVar()
        self.var_item_list = tk.StringVar()
        self.var_sigil_q = tk.StringVar()
        self.var_sigil_name = tk.StringVar()
        self.var_sigil_level = tk.StringVar()
        self.var_sigil_secondary = tk.StringVar()
        self.var_sigil_equip = tk.StringVar()
        self.var_chara = tk.StringVar()
        self.var_chara_slot = tk.StringVar()
        # 召唤石页(新 DLC 背包系统)
        self.var_sum_q = tk.StringVar()
        self.var_sum_slot = tk.StringVar()
        self.var_sum_type = tk.StringVar()
        self.var_sum_main = tk.StringVar()
        self.var_sum_sub = tk.StringVar()
        self.var_sum_mlv = tk.StringVar(value='15')
        self.var_sum_slv = tk.StringVar(value='9')
        self.var_sum_rank = tk.StringVar(value='3')
        self.var_sum_eq = [tk.StringVar(value='(空)') for _ in range(4)]
        self._sum_cur = None          # 当前已读取的召唤石记录
        self._sum_records = []        # 最近一次背包快照
        self._sum_equipped = [0, 0, 0, 0]
        self.var_ld_name = tk.StringVar()
        self.var_ld_chara = tk.StringVar()
        self.var_force = tk.BooleanVar(value=False)

        # 上限突破页
        self.var_om_chara = tk.StringVar(value=_default_chara())
        self.var_om_lane = tk.StringVar(value='0')
        self.var_om_effect = tk.StringVar(value='攻击力')
        self.var_om_value = tk.StringVar(value='1023')
        # 专精/天赋盘页
        self.var_mt_chara = tk.StringVar(value=_default_chara())
        self.var_mt_effect = tk.StringVar()
        self.var_mt_value = tk.StringVar(value='1')
        self.var_mastery_view = tk.StringVar(value='nodes')
        self._mastery_rows = []
        self._mastery_selected_index = None
        self._mastery_saving = False
        self._mastery_pending = {}
        self._mastery_pending_old = {}
        # 小钳蟹页
        self.var_crab_wee = tk.StringVar(value='20')
        self.var_crab_dark = tk.StringVar(value='20')
        self.var_crab_statue = tk.BooleanVar(value=True)
        self.var_crab_quest = tk.BooleanVar(value=True)
        # 武器祝福页
        self.var_wr_type = tk.StringVar(value=gct.WRIGHT_TYPES[0][0])
        self.var_wr_traits = [tk.StringVar() for _ in range(3)]
        self.var_wr_levels = [tk.StringVar(value=str(lv)) for lv in (20, 15, 10)]

        # 状态栏
        self._status_save = tk.StringVar(value='未加载')
        self._status_msg = tk.StringVar(value='就绪')

        # 性能缓存:打开的存档 + 各 id_type 的 vm 字典(打开后记录不变,写档后失效)
        self._save = None
        self._save_path = None
        self._vm_cache = {}
        self._busy = False

        self._build_top()
        self._build_notebook()
        self._build_log()
        self._build_statusbar()

        # 快捷键
        root.bind("<F5>", lambda e: self.refresh_all())
        root.bind("<Control-b>", lambda e: self.backup_save())
        root.bind("<Control-o>", lambda e: self._pick_save())
        root.bind("<Control-h>", lambda e: self._show_about())

        # 关闭时记忆窗口几何
        root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 打开默认存档并刷新
        self.root.after(50, self.refresh_all)

    # ------------------------------------------------------------ 顶部
    def _build_top(self):
            top = ttk.Frame(self.root, padding=(8, 6, 8, 2))
            top.pack(fill="x")
            ttk.Label(top, text=APP_TITLE, font=th.font(12, bold=True), foreground=th.ACCENT).pack(side="left")
            ttk.Label(top, text="v1.4", foreground=th.FG_DIM).pack(side="right")

            row = ttk.Frame(self.root, padding=(8, 2, 8, 6))
            row.pack(fill="x")
            force = ttk.Checkbutton(row, text="强制写入(有风险)", variable=self.var_force)
            refresh = ttk.Button(row, text="打开并刷新", style="Accent.TButton", command=self.refresh_all)
            refresh.pack(side="right", padx=(0, 8))
            force.pack(side="right", padx=4)
            ttk.Label(row, text="存档路径:").pack(side="left")
            ttk.Entry(row, textvariable=self.save_path, width=52).pack(side="left", padx=4)
            ttk.Button(row, text="浏览…", command=self._pick_save).pack(side="left")
            ttk.Button(row, text="备份当前存档", command=self.backup_save).pack(side="left")
            ttk.Button(row, text="关于", command=self._show_about).pack(side="left")


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
            self._tab_mastery(nb)
            self._tab_crab(nb)
            self._tab_wrightstone(nb)
            self.nb = nb


    def _mk_out(self, parent, height):
        t = tk.Text(
            parent,
            height=height,
            state="disabled",
            wrap="none",
            relief="flat",
            bg=th.BG_TEXT,
            fg=th.FG,
            insertbackground=th.ACCENT,
            font=th.mono_font(9),
        )
        th.configure_tags(t)
        t.pack(fill="both", expand=True, pady=(6, 0))
        sb = ttk.Scrollbar(parent, command=t.yview, style="Vertical.TScrollbar")
        t.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        return t


    def _chara_cb(self, parent, var, width=16):
        choices = _chara_choices()
        cb = ttk.Combobox(
            parent,
            textvariable=var,
            width=width,
            state="normal",
            values=choices,
        )
        return cb


    def _tab_items(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 物品 ")
        top = ttk.Frame(t)
        top.pack(fill="x")
        ttk.Label(top, text="搜索:").pack(side="left", padx=(0, 4))
        ttk.Entry(top, textvariable=self.var_item_q, width=22).pack(side="left", padx=(0, 8))
        ttk.Button(top, text="列出", command=self.cmd_items_list).pack(side="left")
        ttk.Label(top, text="修改(名称 数量):").pack(side="left", padx=(16, 4))
        ttk.Entry(top, textvariable=self.var_item_list, width=26).pack(side="left", padx=(0, 8))
        ttk.Button(top, text="设置数量", style="Accent.TButton", command=self.cmd_items_set).pack(side="left")
        self.items_out = self._mk_out(t, 15)


    def _tab_sigils(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 因子 ")
        top = ttk.Frame(t)
        top.pack(fill="x")
        ttk.Label(top, text="搜索:").pack(side="left", padx=(0, 4))
        ttk.Entry(top, textvariable=self.var_sigil_q, width=22).pack(side="left", padx=(0, 8))
        ttk.Button(top, text="列出", command=self.cmd_sigils_list).pack(side="left")
        mid = ttk.LabelFrame(t, text="生成合法因子", padding=8)
        mid.pack(fill="x", pady=6)
        g = ttk.Frame(mid)
        g.pack(fill="x")
        ttk.Label(g, text="因子(名称/0x):").pack(side="left", padx=(0, 4))
        ttk.Entry(g, textvariable=self.var_sigil_name, width=26).pack(side="left", padx=(0, 8))
        ttk.Label(g, text="等级:").pack(side="left", padx=(0, 4))
        ttk.Entry(g, textvariable=self.var_sigil_level, width=5).pack(side="left", padx=(0, 8))
        ttk.Label(g, text="副词条:").pack(side="left", padx=(0, 4))
        ttk.Entry(g, textvariable=self.var_sigil_secondary, width=16).pack(side="left", padx=(0, 8))
        ttk.Label(g, text="装备给:").pack(side="left", padx=(0, 4))
        self._chara_cb(g, self.var_sigil_equip, width=16).pack(side="left")
        b = ttk.Frame(mid)
        b.pack(fill="x", pady=(6, 0))
        ttk.Button(b, text="生成(写入存档)", style="Accent.TButton", command=self.cmd_sigils_add).pack(side="left", padx=(0, 8))
        ttk.Button(b, text="预览(不写入)", command=self.cmd_sigils_add_dry).pack(side="left")
        self.sigils_out = self._mk_out(t, 10)


    def _tab_chars(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 角色 ")
        top = ttk.Frame(t)
        top.pack(fill="x")
        ttk.Label(top, text="角色:").pack(side="left", padx=(0, 4))
        self._chara_cb(top, self.var_chara, 16).pack(side="left", padx=(0, 8))
        ttk.Button(top, text="列出装备", command=self.cmd_chars_list).pack(side="left", padx=(0, 8))
        ttk.Button(top, text="查看该角色因子", command=self.cmd_chars_sigils).pack(side="left", padx=(0, 8))
        ttk.Label(top, text="槽号:").pack(side="left", padx=(0, 4))
        ttk.Entry(top, textvariable=self.var_chara_slot, width=7).pack(side="left", padx=(0, 4))
        ttk.Button(top, text="卸下指定", command=self.cmd_chars_unequip).pack(side="left", padx=(0, 8))
        ttk.Button(top, text="卸下全部", style="Danger.TButton", command=self.cmd_chars_clear).pack(side="left")
        self.chars_out = self._mk_out(t, 16)


    def _tab_summons(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 召唤石 ")
        top = ttk.Frame(t)
        top.pack(fill="x")
        ttk.Button(top, text="列出召唤石", command=self.cmd_summons_list).pack(side="left", padx=(0, 8))
        ttk.Label(top, text="搜索:").pack(side="left", padx=(0, 4))
        ttk.Entry(top, textvariable=self.var_sum_q, width=18).pack(side="left", padx=(0, 8))

        edit = ttk.LabelFrame(t, text="编辑召唤石(槽号取自列表第一列,点\"读取\"载入)", padding=8)
        edit.pack(fill="x", pady=6)
        g = ttk.Frame(edit)
        g.pack(fill="x")
        ttk.Label(g, text="槽号:").pack(side="left", padx=(0, 4))
        ttk.Entry(g, textvariable=self.var_sum_slot, width=6).pack(side="left", padx=(0, 4))
        ttk.Button(g, text="读取", command=self.cmd_summons_load).pack(side="left", padx=(0, 8))
        ttk.Label(g, text="种类:").pack(side="left", padx=(0, 4))
        self._sum_type_cb = ttk.Combobox(g, textvariable=self.var_sum_type, width=26, state="normal")
        self._sum_type_cb.pack(side="left", padx=(0, 8))
        ttk.Label(g, text="主加护:").pack(side="left", padx=(0, 4))
        self._sum_main_cb = ttk.Combobox(g, textvariable=self.var_sum_main, width=20, state="normal")
        self._sum_main_cb.pack(side="left", padx=(0, 8))
        g2 = ttk.Frame(edit)
        g2.pack(fill="x", pady=(4, 0))
        ttk.Label(g2, text="副词条:").pack(side="left", padx=(0, 4))
        self._sum_sub_cb = ttk.Combobox(g2, textvariable=self.var_sum_sub, width=26, state="normal")
        self._sum_sub_cb.pack(side="left", padx=(0, 8))
        ttk.Label(g2, text="主级:").pack(side="left", padx=(0, 4))
        ttk.Entry(g2, textvariable=self.var_sum_mlv, width=4).pack(side="left", padx=(0, 8))
        ttk.Label(g2, text="副档:").pack(side="left", padx=(0, 4))
        ttk.Entry(g2, textvariable=self.var_sum_slv, width=4).pack(side="left", padx=(0, 8))
        ttk.Label(g2, text="阶级:").pack(side="left", padx=(0, 4))
        ttk.Entry(g2, textvariable=self.var_sum_rank, width=4).pack(side="left", padx=(0, 8))
        ttk.Button(g2, text="更新该石", style="Accent.TButton", command=self.cmd_summons_set).pack(side="left", padx=(0, 8))
        ttk.Button(g2, text="新增召唤石", command=lambda: self.cmd_summons_add(dry=False)).pack(side="left", padx=(0, 8))
        ttk.Button(g2, text="预览新增", command=lambda: self.cmd_summons_add(dry=True)).pack(side="left")

        eq = ttk.LabelFrame(t, text="装备(4 个召唤石槽,★ = 已装备)", padding=8)
        eq.pack(fill="x", pady=6)
        eqrow = ttk.Frame(eq)
        eqrow.pack(fill="x")
        self._sum_eq_cbs = []
        for i in range(4):
            ttk.Label(eqrow, text=f"槽{i+1}:").pack(side="left", padx=(4, 2))
            cb = ttk.Combobox(eqrow, textvariable=self.var_sum_eq[i], width=28, state="readonly")
            cb.pack(side="left", padx=(0, 6))
            self._sum_eq_cbs.append(cb)
        ttk.Button(eqrow, text="应用装备", style="Accent.TButton", command=self.cmd_summons_equip).pack(side="left", padx=6)
        ttk.Button(eqrow, text="卸下全部", style="Danger.TButton", command=self.cmd_summons_unequip_all).pack(side="left", padx=6)
        self.summons_out = self._mk_out(t, 10)

        # 种类变化时,把该种类的天然词池排到主加护/副词条下拉最前
        self._sum_type_cb.bind('<<ComboboxSelected>>', self._sum_type_changed)
        # 初始填充下拉选项
        self._sum_refresh_combos()


    def _tab_loadout(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 配装方案 ")
        top = ttk.Frame(t)
        top.pack(fill="x")
        ttk.Button(top, text="列出方案", command=self.cmd_ld_list).pack(side="left", padx=(0, 8))
        ttk.Label(top, text="方案名:").pack(side="left", padx=(0, 4))
        ttk.Entry(top, textvariable=self.var_ld_name, width=14).pack(side="left", padx=(0, 8))
        ttk.Label(top, text="角色:").pack(side="left", padx=(0, 4))
        self._chara_cb(top, self.var_ld_chara, 16).pack(side="left", padx=(0, 8))
        ttk.Button(top, text="保存方案", style="Accent.TButton", command=self.cmd_ld_save).pack(side="left", padx=(0, 8))
        ttk.Button(top, text="恢复方案", command=self.cmd_ld_restore).pack(side="left")
        self.ld_out = self._mk_out(t, 16)


    # ------------------------------------------------------------ 日志
    def _build_log(self):
        lf = ttk.LabelFrame(self.root, text="日志", padding=(6, 3))
        lf.pack(fill="x", padx=8, pady=6)
        self.log = tk.Text(
            lf,
            height=9,
            state="disabled",
            wrap="none",
            relief="flat",
            bg=th.BG_TEXT,
            fg=th.FG,
            insertbackground=th.ACCENT,
            font=th.mono_font(9),
        )
        sb = ttk.Scrollbar(lf, orient="vertical", style="Vertical.TScrollbar", command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(side="left", fill="x", expand=True)
        th.configure_tags(self.log)
        self._capture = LogCapture(self.log)


    def _note(self, s):
        self._capture.write(s + "\n")

    def _open(self):
        """带缓存的存档打开:路径不变则复用已打开的存档对象(避免每次 2.3s 重开)。"""
        p = self.save_path.get().strip()
        if not os.path.isfile(p):
            self._note(f'[错误] 找不到存档: {p}')
            self._status_msg.set('打开失败: 找不到存档')
            return None
        if self._save is not None and self._save_path == p:
            return self._save
        try:
            self._save = gct.GBFRSaveData.open(p)
            self._save_path = p
            self._vm_cache = {}
            self._status_save.set(os.path.basename(p))
            return self._save
        except Exception as e:
            self._note(f'[错误] 打开存档失败: {e}')
            self._status_msg.set(f'打开失败: {e}')
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
        self._sum_refresh(save)
        self._summons_list(save)
        self._ld_list()
        self._mastery_refresh(save)
        self._note('--- 已刷新 ---')
        self._status_msg.set('已加载并刷新 ✓')

    def backup_save(self):
        import shutil, time
        p = self.save_path.get().strip()
        if not os.path.isfile(p):
            self._note(f'[错误] 找不到存档: {p}')
            self._status_msg.set('备份失败: 找不到存档')
            return
        bak = f'{p}.manual_{time.strftime("%Y%m%d_%H%M%S")}'
        shutil.copy2(p, bak)
        self._note(f'[完成] 已备份: {os.path.basename(bak)}')
        self._status_msg.set(f'已备份: {os.path.basename(bak)}')

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
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'item', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
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
        primary = gct.sigil_primary_hash(gem_hash, info)
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
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'sigil', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
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
            t2 = m1701.get(gct.TRAIT_REC_BASE + idx * 100 + 1)
            name = (e.get('cn') or e.get('name')) if e else f'0x{g:08X}'
            line = f'  槽{u}: {name:<24} lv{m2704.get(u)}'
            if t1:
                line += f'  主:{gct.sigil_trait_label(t1)}'
            if t2:
                line += f'  副:{gct.sigil_trait_label(t2)}'
            lines.append(line)
        self._set_text(self.chars_out, '\n'.join(lines) if len(lines) > 1 else f'{gct.chara_label(gid)} 未装备因子')

    def cmd_chars_unequip(self):
        save = self._open()
        if save is None:
            return
        ch_hash, gid = gct.find_chara(self.var_chara.get().strip())
        if ch_hash is None:
            self._note(f'[错误] 找不到角色: {self.var_chara.get().strip()}'); return
        slot_s = self.var_chara_slot.get().strip()
        if not slot_s or not slot_s.lstrip('-').isdigit():
            self._note('[错误] 请输入要卸下的槽号(查看角色因子时会显示槽号)'); return
        slot = int(slot_s)
        m2703 = self._vm(gct.ID_2703); m2706 = self._vm(gct.ID_2706); m2702 = self._vm(gct.ID_2702)
        if slot not in m2703 or (m2703.get(slot, gct.EMPTY) & 0xFFFFFFFF) == gct.EMPTY:
            self._note(f'[错误] 槽 {slot} 为空'); return
        if (m2706.get(slot, 0) & 0xFFFFFFFF) != (ch_hash & 0xFFFFFFFF):
            self._note(f'[错误] 槽 {slot} 不是 {gct.chara_label(gid)} 的因子'); return
        gct.set_first(save, gct.ID_2706, slot, gct.EMPTY, 'uint')
        gct.sigil_equip_unregister(save, ch_hash, m2702.get(slot, 0))
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'unequip', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
        self._invalidate()
        self._note(f'[完成] 槽{slot} 已从 {gct.chara_label(gid)} 卸下 备份:{os.path.basename(bak)}')

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
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'unequip', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
        self._invalidate()
        self._note(f'[完成] 已卸下 {gct.chara_label(gid)} 的 {changed} 个因子 备份:{os.path.basename(bak)}')

    # ------------------------------------------------------------ 召唤石
    def _sum_full_names(self, which):
        """目录全量显示名列表(用于下拉框,含 0x 哈希以便区分同名)。"""
        cat = gct.SUMCAT_MAIN if which == 'main' else gct.SUMCAT_SUB
        out = []
        for hk, e in sorted(cat.items()):
            cn = e.get('cn') or ''
            en = e.get('en') or ''
            tag = ' (%s)' % en if en and cn else ''
            out.append('%s%s [0x%08X]' % (cn or '0x%08X' % (int(hk) & 0xFFFFFFFF), tag, int(hk) & 0xFFFFFFFF))
        return out

    def _sum_natural_names(self, type_hash, which):
        """某种类的 2.0.2 天然词池显示名(含 0x 哈希)。"""
        te = gct.SUMCAT_TYPES.get(gct._sum_key(type_hash), {})
        names = []
        if which == 'main':
            for h in te.get('mainTraitHashes', []):
                n = '%s [0x%08X]' % (gct.summon_trait_name(h), int(h) & 0xFFFFFFFF)
                if n not in names:
                    names.append(n)
        else:
            for h in te.get('subParamHashes', []):
                n = '%s [0x%08X]' % (gct.summon_sub_name(h), int(h) & 0xFFFFFFFF)
                if n not in names:
                    names.append(n)
        return names

    def _sum_refresh_combos(self):
        """刷新种类/主加护/副词条下拉(天然词池排前,保留当前值)。"""
        all_types = []
        for hk, e in sorted(gct.SUMCAT_TYPES.items()):
            cn = e.get('cn') or ''
            en = e.get('en') or ''
            tag = ' (%s)' % en if en and cn else ''
            all_types.append('%s%s [0x%08X]' % (cn, tag, int(hk) & 0xFFFFFFFF))
        cur_t = self.var_sum_type.get()
        self._sum_type_cb.configure(values=all_types)
        if cur_t:
            self.var_sum_type.set(cur_t)
        th = gct.summon_find_type(cur_t) if cur_t else None
        pool_m = self._sum_natural_names(th, 'main') if th else []
        pool_s = self._sum_natural_names(th, 'sub') if th else []
        all_m = self._sum_full_names('main')
        all_s = self._sum_full_names('sub')
        vals_m = pool_m + [x for x in all_m if x not in pool_m]
        vals_s = pool_s + [x for x in all_s if x not in pool_s]
        cur_m = self.var_sum_main.get()
        cur_s = self.var_sum_sub.get()
        self._sum_main_cb.configure(values=vals_m)
        self._sum_sub_cb.configure(values=vals_s)
        if cur_m:
            self.var_sum_main.set(cur_m)
        if cur_s:
            self.var_sum_sub.set(cur_s)

    def _sum_type_changed(self, event=None):
        self._sum_refresh_combos()

    def cmd_summons_list(self):
        save = self._open()
        if save is None:
            return
        self._sum_refresh(save)
        self._summons_list(save)

    def _sum_refresh(self, save):
        """刷新背包快照 + 装备下拉。返回 save。"""
        records, equipped, max_slot, unlocked = gct.summon_inventory(save)
        self._sum_records = records
        self._sum_equipped = [int(v) & 0xFFFFFFFF for v in equipped]
        self._sum_unlocked = unlocked
        self._sum_max_slot = max_slot
        name_by_slot = {r['slot']: '槽%d · %s' % (r['slot'], gct.summon_type_name(r['type_hash'])) for r in records}
        eq_vals = ['(空)'] + [name_by_slot[s] for s in sorted(name_by_slot)]
        for i, cb in enumerate(self._sum_eq_cbs):
            cb.configure(values=eq_vals)
            cur = self._sum_equipped[i] if i < len(self._sum_equipped) else 0
            self.var_sum_eq[i].set(name_by_slot.get(cur, '(空)') if cur else '(空)')
        return save

    def _summons_list(self, save):
        self._set_text(self.summons_out, '')
        q = self.var_sum_q.get().strip().lower()
        eq_set = set(self._sum_equipped)
        lines = ['=== 召唤石背包(%d 个%s) ===' % (
            len(self._sum_records), ' · 已解锁' if getattr(self, '_sum_unlocked', False) else ' · 未解锁')]
        for r in self._sum_records:
            tn = gct.summon_type_name(r['type_hash'])
            mn = gct.summon_trait_name(r['main_hash'])
            sn = gct.summon_sub_name(r['sub_hash'])
            if q and q not in tn.lower() and q not in mn.lower() and q not in sn.lower() and \
                    q not in f'0x{r["type_hash"]:08X}'.lower():
                continue
            mark = '★' if r['slot'] in eq_set else ' '
            lines.append('  %s槽%-4d %-30s 主:%s Lv%-2d 副:%s 档%-2d 阶级%d' % (
                mark, r['slot'], tn, mn, r['main_level'], sn, r['sub_level'], r['rank']))
        self._set_text(self.summons_out, '\n'.join(lines) if len(lines) > 1 else '(无召唤石)')

    def cmd_summons_load(self):
        save = self._open()
        if save is None:
            return
        self._sum_refresh(save)
        q = self.var_sum_slot.get().strip()
        if not q or not q.lstrip('-').isdigit():
            self._note('[错误] 请输入槽号(列表第一列数字)'); return
        slot = int(q)
        rec = next((r for r in self._sum_records if r['slot'] == slot), None)
        if rec is None:
            rec = gct.summon_read_record(save, slot)  # 兼容直接输入 unit
        if rec is None:
            self._note(f'[错误] 找不到槽 {q} 对应的召唤石'); return
        self._sum_cur = rec
        self.var_sum_slot.set(str(rec['slot']))
        self.var_sum_type.set(gct.summon_type_name(rec['type_hash']))
        self._sum_refresh_combos()
        self.var_sum_main.set(gct.summon_trait_name(rec['main_hash']))
        self.var_sum_sub.set(gct.summon_sub_name(rec['sub_hash']))
        self.var_sum_mlv.set(str(rec['main_level']))
        self.var_sum_slv.set(str(rec['sub_level']))
        self.var_sum_rank.set(str(rec['rank']))
        self._note(f'[信息] 已读取槽{rec["slot"]} (unit {rec["unit"]}): {gct.summon_type_name(rec["type_hash"])}')

    def _sum_form_values(self):
        """从表单解析 (type_h, main_h, sub_h, ml, sl, rank);失败返回 (None, 错误)。"""
        th = gct.summon_find_type(self.var_sum_type.get().strip())
        if th is None:
            return None, '找不到召唤石种类: %s' % self.var_sum_type.get().strip()
        mh = gct.summon_find_main(self.var_sum_main.get().strip())
        if mh is None:
            return None, '找不到主加护: %s' % self.var_sum_main.get().strip()
        sh = gct.summon_find_sub(self.var_sum_sub.get().strip())
        if sh is None:
            return None, '找不到副词条: %s' % self.var_sum_sub.get().strip()
        try:
            ml = int(self.var_sum_mlv.get().strip())
            sl = int(self.var_sum_slv.get().strip())
            rank = int(self.var_sum_rank.get().strip())
        except ValueError:
            return None, '主级/副档/阶级必须是整数'
        return (th, mh, sh, ml, sl, rank), None

    def cmd_summons_set(self):
        save = self._open()
        if save is None:
            return
        self._sum_refresh(save)
        if self._sum_cur is None:
            self._note('[错误] 请先在槽号输入框输入槽号并点"读取"'); return
        vals, err = self._sum_form_values()
        if err:
            self._note(f'[错误] {err}'); return
        th, mh, sh, ml, sl, rank = vals
        verr, warns = gct.summon_validate_draft(th, mh, sh, ml, sl, rank, natural_warn=True)
        if verr:
            self._note(f'[错误] {verr}'); return
        for w in warns:
            self._note(f'[警告] {w}')
        err2, upd = gct.summon_update(save, self._sum_cur['unit'], th, mh, sh, ml, sl, rank)
        if err2:
            self._note(f'[错误] {err2}'); return
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'summon', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
        self._invalidate()
        self._note('[完成] 槽%d 已更新: %s 主:%s Lv%d 副:%s 档%d 阶级%d 备份:%s' % (
            upd['slot'], gct.summon_type_name(upd['type_hash']),
            gct.summon_trait_name(upd['main_hash']), upd['main_level'],
            gct.summon_sub_name(upd['sub_hash']), upd['sub_level'], upd['rank'],
            os.path.basename(bak)))
        self._sum_cur = upd
        self.var_sum_slot.set(str(upd['slot']))
        self._sum_refresh(save)
        self._summons_list(save)

    def cmd_summons_add(self, dry=False):
        save = self._open()
        if save is None:
            return
        self._sum_refresh(save)
        vals, err = self._sum_form_values()
        if err:
            self._note(f'[错误] {err}'); return
        th, mh, sh, ml, sl, rank = vals
        verr, warns = gct.summon_validate_draft(th, mh, sh, ml, sl, rank, natural_warn=True)
        if verr:
            self._note(f'[错误] {verr}'); return
        for w in warns:
            self._note(f'[警告] {w}')
        err2, rec = gct.summon_create(save, th, mh, sh, ml, sl, rank, dry=dry)
        if err2:
            self._note(f'[错误] {err2}'); return
        if dry:
            self._note('[预览] 将新增: %s 主:%s Lv%d 副:%s 档%d 阶级%d (槽%d)' % (
                gct.summon_type_name(rec['type_hash']), gct.summon_trait_name(rec['main_hash']),
                rec['main_level'], gct.summon_sub_name(rec['sub_hash']), rec['sub_level'],
                rec['rank'], rec['slot']))
            return
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'summon', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
        self._invalidate()
        self._note('[完成] 已新增: %s (槽%d) 备份:%s' % (
            gct.summon_type_name(rec['type_hash']), rec['slot'], os.path.basename(bak)))
        self._sum_refresh(save)
        self._summons_list(save)

    def cmd_summons_equip(self):
        save = self._open()
        if save is None:
            return
        # 注意:先读下拉选择,再刷新(_sum_refresh 会把下拉重置为当前装备状态)
        new_eq = []
        for i in range(4):
            s = self.var_sum_eq[i].get().strip()
            if not s or s == '(空)':
                new_eq.append(0)
            else:
                try:
                    new_eq.append(int(s.split(' · ')[0][1:]))
                except (ValueError, IndexError):
                    self._note(f'[错误] 装备槽{i+1} 选择无效: {s}'); return
        self._sum_refresh(save)
        eq_recs = save.find(id_type=gct.ID_SUM_EQUIPPED)
        if not eq_recs:
            self._note('[错误] 存档缺少 1451 装备字段'); return
        save.set_values(eq_recs[0], new_eq)
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'summon_equip', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
        self._invalidate()
        names = {r['slot']: gct.summon_type_name(r['type_hash']) for r in self._sum_records}
        self._note('[完成] 装备已更新: ' + ' | '.join(
            ('槽%d: %s' % (i + 1, names.get(new_eq[i], '空')) if new_eq[i] else '槽%d: 空' % (i + 1))
            for i in range(4)) + ' 备份:%s' % os.path.basename(bak))
        self._sum_refresh(save)
        self._summons_list(save)

    def cmd_summons_unequip_all(self):
        save = self._open()
        if save is None:
            return
        eq_recs = save.find(id_type=gct.ID_SUM_EQUIPPED)
        if not eq_recs:
            self._note('[错误] 存档缺少 1451 装备字段'); return
        save.set_values(eq_recs[0], [0, 0, 0, 0])
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'summon_unequip', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
        self._invalidate()
        self._note(f'[完成] 4 个装备槽已全部卸下 备份:{os.path.basename(bak)}')
        self._sum_refresh(save)
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
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'loadout', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
        self._invalidate()
        self._note(f'[完成] 已恢复配装 {name} 到 {gct.chara_label(gid)} (装备 {ok}/{len(data.get("sigils",[]))}) 备份:{os.path.basename(bak)}')

    def _tab_overmastery(self, nb):
            t = ttk.Frame(nb, padding=8);nb.add(t, text=" 上限突破 ")
            top = ttk.Frame(t)
            top.pack(fill="x", pady=(0,6))
            ttk.Label(top, text="角色:").pack(side="left")
            cb = self._chara_cb(top, self.var_om_chara, 16)
            if cb is not None and not cb.winfo_manager():
                cb.pack(side="left", padx=4)
            ttk.Button(top, text="读取该角色", command=self.cmd_om_list).pack(side="left", padx=4)
            ttk.Label(top, text="槽位(0-3):").pack(side="left", padx=(12,0))
            ttk.Entry(top, textvariable=self.var_om_lane, width=4).pack(side="left", padx=4)
            ttk.Label(top, text="效果:").pack(side="left", padx=(12,0))
            ttk.Combobox(top, textvariable=self.var_om_effect, width=16, state="normal", values=list(gct.OM_EFFECTS.keys())).pack(side="left", padx=4)
            ttk.Label(top, text="数值:").pack(side="left", padx=(12,0))
            ttk.Entry(top, textvariable=self.var_om_value, width=6).pack(side="left", padx=4)
            ttk.Button(top, text="写入该槽", style="Accent.TButton", command=self.cmd_om_set).pack(side="left", padx=4)
            ttk.Button(top, text="清空该槽", style="Danger.TButton", command=self.cmd_om_clear).pack(side="left", padx=4)
            ttk.Button(top, text="全部清空", style="Danger.TButton", command=self.cmd_om_clear_all).pack(side="left", padx=4)
            self.om_out = self._mk_out(t, 14)


    def _tab_mastery(self, nb):
        t = ttk.Frame(nb, padding=8)
        nb.add(t, text=" 专精/天赋 ")
        top = ttk.Frame(t)
        top.pack(fill="x", pady=(0, 6))
        ttk.Label(top, text="角色:").pack(side="left")
        cb = self._chara_cb(top, self.var_mt_chara, 16)
        if cb is not None and not cb.winfo_manager():
            cb.pack(side="left", padx=4)
        cb.bind('<<ComboboxSelected>>', lambda e: self.cmd_mastery_list())
        ttk.Button(top, text="读取该角色专精/天赋", style="Accent.TButton", command=self.cmd_mastery_list).pack(side="left", padx=4)
        ttk.Button(top, text="选中行写入", command=self.cmd_mastery_apply).pack(side="left", padx=4)
        ttk.Button(top, text="一键点亮因子栏位解锁(13格)", command=self.cmd_mastery_enable_slot).pack(side="left", padx=4)

        # 专精技能常用操作(单独一行,避免窗口窄时按钮被挤到屏幕外)
        ops = ttk.Frame(t)
        ops.pack(fill="x", pady=(0, 4))
        ttk.Button(ops, text="激活选中", style="Accent.TButton", command=self.cmd_mastery_activate).pack(side="left", padx=4)
        ttk.Button(ops, text="清空选中行", style="Danger.TButton", command=self.cmd_mastery_clear).pack(side="left", padx=4)
        ttk.Button(ops, text="一键清空当前角色专精技能", style="Danger.TButton", command=self.cmd_mastery_clear_all).pack(side="left", padx=4)

        # 视图切换:默认“节点图”,需要看原始字段可切“列表”
        view = ttk.Frame(t)
        view.pack(fill="x", pady=(0, 4))
        ttk.Label(view, text="视图:").pack(side="left")
        ttk.Radiobutton(view, text="节点图(游戏感)", variable=self.var_mastery_view, value="nodes", command=self._mastery_show_view).pack(side="left", padx=4)
        ttk.Radiobutton(view, text="原始列表", variable=self.var_mastery_view, value="table", command=self._mastery_show_view).pack(side="left", padx=4)
        self.mastery_node_info = ttk.Label(view, text="点击节点选择,双击/下方按钮写入。", foreground=th.FG_DIM)
        self.mastery_node_info.pack(side="right")

        # 表格:列出存档中已存在的 1606/1607 天赋行,双击可直接点亮/取消
        body = ttk.Frame(t)
        body.pack(fill="both", expand=True, pady=(0, 4))
        cols = ("no", "node", "effect", "state", "slotinfo", "hash", "unit")
        tree_frame = ttk.Frame(body)
        self.mastery_tree_frame = tree_frame
        self.mastery_tree = ttk.Treeview(tree_frame, columns=cols, show="headings", height=12)
        headings = {
            "no": "行",
            "node": "专精阶",
            "effect": "专精技能",
            "state": "状态/数值",
            "slotinfo": "流派",
            "hash": "节点哈希",
            "unit": "Save Unit",
        }
        widths = {"no": 40, "node": 80, "effect": 240, "state": 100, "slotinfo": 70, "hash": 90, "unit": 90}
        for c in cols:
            self.mastery_tree.heading(c, text=headings[c])
            self.mastery_tree.column(c, width=widths[c], anchor="w", stretch=(c in ("effect", "slotinfo")))
        self._mastery_vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.mastery_tree.yview)
        self.mastery_tree.configure(yscrollcommand=self._mastery_vsb.set)
        self._mastery_vsb.pack(side="right", fill="y")
        self.mastery_tree.pack(side="left", fill="both", expand=True)
        self.mastery_tree.bind("<<TreeviewSelect>>", self._mastery_on_select)
        self.mastery_tree.bind("<Double-1>", lambda e: self.cmd_mastery_toggle())

        # 节点图:用 Canvas 画可点击的“天赋球”,越接近游戏里一眼看状态
        node_frame = ttk.Frame(body)
        self.mastery_node_frame = node_frame
        self.mastery_node_canvas = tk.Canvas(
            node_frame,
            bg=th.BG_TEXT,
            highlightthickness=0,
            height=420,
        )
        self._mastery_canvas_vsb = ttk.Scrollbar(node_frame, orient="vertical", command=self.mastery_node_canvas.yview)
        self._mastery_canvas_hsb = ttk.Scrollbar(node_frame, orient="horizontal", command=self.mastery_node_canvas.xview)
        self.mastery_node_canvas.configure(xscrollcommand=self._mastery_canvas_hsb.set, yscrollcommand=self._mastery_canvas_vsb.set)
        self._mastery_canvas_hsb.pack(side="bottom", fill="x")
        self._mastery_canvas_vsb.pack(side="right", fill="y")
        self.mastery_node_canvas.pack(side="left", fill="both", expand=True)
        self.mastery_node_canvas.bind("<Button-1>", self._mastery_canvas_click)
        self.mastery_node_canvas.bind("<Double-1>", self._mastery_canvas_double)
        self.mastery_node_canvas.bind("<MouseWheel>", self._mastery_on_mousewheel)
        self.mastery_node_canvas.bind("<Button-4>", lambda e: self.mastery_node_canvas.yview_scroll(-2, "units"))
        self.mastery_node_canvas.bind("<Button-5>", lambda e: self.mastery_node_canvas.yview_scroll(2, "units"))

        self._mastery_show_view()

        edit = ttk.Frame(t)
        edit.pack(fill="x", pady=(4, 0))
        ttk.Label(edit, text="效果(留空=保持当前,0x哈希/中文/英文):").pack(side="left")
        ttk.Entry(edit, textvariable=self.var_mt_effect, width=34).pack(side="left", padx=4)
        ttk.Label(edit, text="状态/数值(1=点亮):").pack(side="left", padx=(8, 0))
        ttk.Entry(edit, textvariable=self.var_mt_value, width=12).pack(side="left", padx=4)
        ttk.Button(edit, text="写入选中行", command=self.cmd_mastery_apply).pack(side="left", padx=8)


    def _tab_crab(self, nb):
        t = ttk.Frame(nb, padding=8);nb.add(t, text=" 小钳蟹 ")
        top = ttk.Frame(t)
        top.pack(fill="x", pady=(0,6))
        ttk.Label(top, text="普通小钳蟹数量:").pack(side="left")
        ttk.Entry(top, textvariable=self.var_crab_wee, width=6).pack(side="left", padx=4)
        ttk.Label(top, text="漆黑小钳蟹数量:").pack(side="left", padx=(10,0))
        ttk.Entry(top, textvariable=self.var_crab_dark, width=6).pack(side="left", padx=4)
        ttk.Checkbutton(top, text="漆黑蟹像=1", variable=self.var_crab_statue).pack(side="left", padx=8)
        ttk.Checkbutton(top, text="完成收集任务", variable=self.var_crab_quest).pack(side="left", padx=8)
        ttk.Button(top, text="执行小钳蟹修改", style="Accent.TButton", command=self.cmd_crab_run).pack(side="left", padx=8)
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
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'overmastery', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
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
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'overmastery', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
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
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'overmastery', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
        self._invalidate()
        _, _gid = gct.find_chara(ch)
        disp = gct.chara_label(_gid) if _gid else ch
        self._note(f'[完成] {disp} 全部 4 槽上限突破已清空 备份:{os.path.basename(bak)}')
        self.cmd_om_list()

    # ------------------------------------------------------------ 专精/天赋
    def _selected_mastery_meta(self):
        if self._mastery_selected_index is not None:
            try:
                return self._mastery_rows[self._mastery_selected_index]
            except (ValueError, IndexError):
                pass
        sel = self.mastery_tree.selection()
        if sel:
            try:
                return self._mastery_rows[int(sel[0])]
            except (ValueError, IndexError):
                pass
        return None

    def _mastery_set_selected(self, index):
        try:
            index = int(index)
        except (TypeError, ValueError):
            return
        if not (0 <= index < len(self._mastery_rows)):
            return
        self._mastery_selected_index = index
        try:
            self.mastery_tree.selection_set(str(index))
        except Exception:
            pass
        self._mastery_on_select()

    def _mastery_on_select(self, _event=None):
        if self.var_mastery_view.get() == 'table':
            sel = self.mastery_tree.selection()
            if sel:
                try:
                    self._mastery_selected_index = int(sel[0])
                except (ValueError, IndexError):
                    pass
        meta = self._selected_mastery_meta()
        if meta is None:
            return
        self.var_mt_effect.set(f'0x{meta["effect"]:08X}' if meta['effect'] not in (0, gct.EMPTY) else '')
        self.var_mt_value.set(str(meta['value']))
        if hasattr(self, 'mastery_node_info'):
            eff = self._mastery_strip_style_prefix(meta.get('name')) or gct.mastery_effect_name(meta['effect'])
            cat = gct.SKILLBOARD_CAT_NAMES[meta['cat']] if 0 <= int(meta['cat']) < 3 else str(meta['cat'])
            grp = self._mastery_grp_label(meta['grp'])
            self.mastery_node_info.configure(text=f'当前: {cat}  {grp}  {eff}  {gct.mastery_value_label(meta["value"])}  unit {meta["unit"]}')
    def _mastery_unit_belongs_to_chara(self, save, ch, unit):
        """防止切换下拉后误把上一个角色的行写进新角色。"""
        group = gct.char_group(ch, save=save)
        if group is None:
            return False
        base = gct.mastery_board_base(group)
        return base <= int(unit) < base + gct.MASTERY_BOARD_SLOT_COUNT

    def _mastery_show_view(self):
        mode = self.var_mastery_view.get()
        if mode == 'table':
            self.mastery_node_frame.pack_forget()
            self.mastery_tree_frame.pack(fill="both", expand=True, pady=(0, 4))
        else:
            self.mastery_tree_frame.pack_forget()
            self.mastery_node_frame.pack(fill="both", expand=True, pady=(0, 4))
        if self._mastery_rows:
            self._mastery_draw_nodes(self._mastery_rows)

    def _mastery_update_scroll(self):
        box = self.mastery_node_canvas.bbox("all")
        if box:
            self.mastery_node_canvas.configure(scrollregion=box)

    def _mastery_node_color(self, r):
        h = int(r['effect'] or 0) & 0xFFFFFFFF
        val = int(r['value'] or 0)
        if h in (0, gct.EMPTY):
            base = "#4a5263"
        elif h == gct.SIGIL_SLOT_UNLOCK_EFFECT:
            base = "#e8c84a"
        elif h in (0x43B7581D, 0x4A4C093D, 0x9C555433, 0x1D58B743, 0x3D094C4A, 0x3354559C):
            base = "#b48ae0"
        elif h in (0xC4925BD7, 0x9A97C049, 0x6CB38EF3, 0x4E42646B, 0x45C65767, 0x68B39018,
                   0xD75B92C4, 0x1890B368, 0x6757C645, 0x6B64424E, 0x49C0979A, 0xF38EB36C):
            base = "#e08a7a"
        elif h in (0x52A207B5, 0x54929589, 0xB507A252, 0x89959254):
            base = "#6ab7e8"
        else:
            base = "#8a94a6"
        if val == 1:
            return base, "#1e2a36", 2
        if val == 0:
            return "#15191f", base, 1
        return "#ff9f43", "#1e2a36", 2

    @staticmethod
    def _mastery_grp_label(grp):
        return {
            0x68DE92AC: '专精阶 I',
            0xA96D9EBC: '专精阶 II',
            0x4A5DDC7B: '专精阶 III',
            0x3B99904D: 'EX',
        }.get(int(grp) & 0xFFFFFFFF, f'阶 {int(grp) & 0xFFFFFFFF:08X}')

    @staticmethod
    def _mastery_strip_style_prefix(name):
        if not name:
            return ''
        for prefix in ('觉醒：', '真谛：', '秘义：'):
            if name.startswith(prefix):
                return name[len(prefix):]
        return name

    def _mastery_draw_nodes(self, rows):
        c = self.mastery_node_canvas
        c.delete("all")
        self._mastery_node_items = []
        self._mastery_node_item_by_index = {}
        self._mastery_node_hit = []
        rows = [(i, r) for i, r in enumerate(rows)]
        if not rows:
            if hasattr(self, 'mastery_node_info'):
                self.mastery_node_info.configure(text="没有可显示的专精技能")
            return
        # 专精技能:纵向=觉醒/真谛/秘义, 横向按专精阶分组,每个阶内每行 2 个技能
        type_names = gct.SKILLBOARD_CAT_NAMES
        type_count = 3
        grp_order = [0x68DE92AC, 0xA96D9EBC, 0x4A5DDC7B, 0x3B99904D]
        left = 96
        top = 96
        type_w = 320
        type_gap = 18
        row_h = 40
        group_h = 28
        group_gap = 10
        radius = 9
        x_offsets = (type_w * 0.28, type_w * 0.72)

        c.create_text(left, 12, anchor="w", fill="#c9d1d9",
                      text="暗色=未点亮/0  亮色=已习得/1或更高  单击未点亮=激活  滚轮=滚动")
        c.create_text(left, 30, anchor="w", fill="#8b949e",
                      text=f"当前角色专精技能 {len(rows)} 个  每行 2 个  行上按专精阶分组")

        max_bottom = top
        for t in range(type_count):
            cat_rows = sorted([(i, r) for i, r in rows if int(r['cat']) == t],
                              key=lambda x: (int(x[1]['pos']), x[0]))
            if not cat_rows:
                continue
            x0 = left + t * (type_w + type_gap)
            x1 = x0 + type_w
            c.create_text(x0 + type_w / 2, top - 30, anchor="n", fill="#e6edf3",
                          text=type_names[t])
            y = top
            for grp in grp_order:
                cell = [(i, r) for i, r in cat_rows if int(r['grp']) == grp]
                if not cell:
                    continue
                # 专精阶分组横条
                c.create_rectangle(x0, y, x1, y + group_h,
                                   outline="#2d3744", fill="#222a36")
                c.create_text(x0 + 12, y + group_h / 2, anchor="w", fill="#c9d1d9",
                              text=self._mastery_grp_label(grp))
                y += group_h
                for n, (i, r) in enumerate(cell):
                    line = n // 2
                    col = n % 2
                    y_node = y + 16 + line * row_h
                    x = x0 + x_offsets[col]
                    is_main = (n == 0)
                    rr = 12 if is_main else radius
                    fill, outline, width = self._mastery_node_color(r)
                    if is_main:
                        # 专精阶大节点:外圈高亮
                        c.create_oval(x - rr - 4, y_node - rr - 4, x + rr + 4, y_node + rr + 4,
                                      outline="#f0b64c", width=2, fill="")
                    item = c.create_oval(x - rr, y_node - rr, x + rr, y_node + rr,
                                         fill=fill, outline=outline, width=width,
                                         tags=("mastery_node", f"node_{i}"))
                    self._mastery_node_items.append(item)
                    self._mastery_node_item_by_index[i] = item
                    name = self._mastery_strip_style_prefix(r.get('name'))
                    if name:
                        c.create_text(x + 14, y_node, anchor="w", fill="#d7dee8",
                                      text=name, font=("Microsoft YaHei UI", 8))
                    # 点击热区:节点 + 右侧文字(仅有名字的节点才加宽)
                    hit_w = max(28, len(name) * 11 + 28) if name else 30
                    self._mastery_node_hit.append((i, x, y_node, hit_w, 16))
                y += ((len(cell) + 1) // 2) * row_h + group_gap
            # 列边框只描边,不遮挡阶分组横条
            c.create_rectangle(x0, top - 4, x1, y + 4,
                               outline="#3a4454", fill="", width=1)
            max_bottom = max(max_bottom, y + 4)

        width = left + type_count * (type_w + type_gap) + 120
        height = max_bottom + 40
        c.configure(scrollregion=(0, 0, width, height))

    def _mastery_canvas_click(self, event):
        x = self.mastery_node_canvas.canvasx(event.x)
        y = self.mastery_node_canvas.canvasy(event.y)
        for index, cx, cy, hw, hh in reversed(getattr(self, '_mastery_node_hit', [])):
            if abs(x - cx) <= hw and abs(y - cy) <= hh:
                self._mastery_set_selected(index)
                if self._mastery_is_main(index):
                    self._note('[信息] 专精阶大节点由该阶已激活技能数自动决定,无需手动点击')
                    return "break"
                meta = self._selected_mastery_meta()
                if meta is not None and int(meta['value'] or 0) == 0:
                    self._mastery_activate_selected()
                return "break"
    def _mastery_apply_visual_state(self, index, value):
        """只更新内存数据/表格/Canvas 节点颜色,不重绘整个节点图。"""
        try:
            index = int(index)
        except (TypeError, ValueError):
            return
        if not (0 <= index < len(self._mastery_rows)):
            return
        self._mastery_rows[index]['value'] = int(value)
        try:
            self.mastery_tree.set(str(index), 'state', gct.mastery_value_label(value))
        except Exception:
            pass
        item = getattr(self, '_mastery_node_item_by_index', {}).get(index)
        if item:
            fill, outline, width = self._mastery_node_color(self._mastery_rows[index])
            self.mastery_node_canvas.itemconfigure(item, fill=fill, outline=outline, width=width)

    def _mastery_index_by_unit(self, unit):
        unit = int(unit)
        for i, r in enumerate(self._mastery_rows):
            if int(r['unit']) == unit:
                return i
        return None

    def _mastery_main_index(self, index):
        """返回该节点所在专精阶的第一个大节点索引;找不到返回 None。"""
        try:
            index = int(index)
        except (TypeError, ValueError):
            return None
        if not (0 <= index < len(self._mastery_rows)):
            return None
        r = self._mastery_rows[index]
        cat = int(r['cat']); grp = int(r['grp'])
        sub = [(i, x) for i, x in enumerate(self._mastery_rows)
               if int(x['cat']) == cat and int(x['grp']) == grp]
        if not sub:
            return None
        return min(sub, key=lambda x: (int(x[1]['pos']), x[0]))[0]

    def _mastery_is_main(self, index):
        return self._mastery_main_index(index) == int(index)

    def _mastery_update_main_nodes(self):
        """根据同一类型同一阶已激活的普通技能数,自动重算大节点状态。"""
        changed = 0
        for cat in range(3):
            for grp, threshold in gct.SKILLBOARD_MAIN_THRESHOLDS.items():
                sub = sorted(
                    [(i, r) for i, r in enumerate(self._mastery_rows)
                     if int(r['cat']) == cat and int(r['grp']) == grp],
                    key=lambda x: (int(x[1]['pos']), x[0]))
                if not sub:
                    continue
                main_i, main_r = sub[0]
                count = sum(1 for _, r in sub[1:] if int(r['value'] or 0) > 0)
                expected = 1 if count >= int(threshold) else 0
                if int(main_r['value'] or 0) != expected:
                    if self._mastery_queue_state(main_i, expected, auto=True):
                        changed += 1
        return changed

    def _mastery_queue_state(self, index, value, auto=False):
        """把状态变更加入待写队列,并立即更新界面。"""
        try:
            index = int(index)
        except (TypeError, ValueError):
            return False
        if not (0 <= index < len(self._mastery_rows)):
            return False
        if self._mastery_is_main(index) and not auto:
            self._note('[信息] 专精阶大节点由该阶已激活技能数自动决定,无需手动点击')
            return False
        r = self._mastery_rows[index]
        unit = int(r['unit'])
        if unit not in self._mastery_pending_old:
            self._mastery_pending_old[unit] = int(r['value'] or 0)
        self._mastery_pending[unit] = int(value)
        self._mastery_apply_visual_state(index, value)
        return True

    def _mastery_discard_pending(self):
        """写档失败时丢弃尚未写入的排队变更,并恢复界面状态。"""
        for unit, old in self._mastery_pending_old.items():
            idx = self._mastery_index_by_unit(unit)
            if idx is not None:
                self._mastery_apply_visual_state(idx, old)
        self._mastery_pending = {}
        self._mastery_pending_old = {}
        self._mastery_on_select()

    def _mastery_flush_pending(self):
        """把队列中的变更写入内存存档,并启动后台写档。"""
        if getattr(self, '_mastery_saving', False):
            return
        if not self._mastery_pending:
            return
        save = self._open()
        if save is None:
            return
        batch = self._mastery_pending
        batch_old = self._mastery_pending_old
        self._mastery_pending = {}
        self._mastery_pending_old = {}
        for unit, value in batch.items():
            err = gct.set_mastery_state(save, unit, value)
            if err:
                # 内存写入失败,回滚已应用的部分
                for u, v in batch_old.items():
                    idx = self._mastery_index_by_unit(u)
                    if idx is not None:
                        self._mastery_apply_visual_state(idx, v)
                self._note(f'[错误] {err}')
                return
        self.root.update_idletasks()

        def done(bak, save_err):
            if save_err:
                for unit, old in batch_old.items():
                    idx = self._mastery_index_by_unit(unit)
                    if idx is not None:
                        self._mastery_apply_visual_state(idx, old)
                self._mastery_on_select()
                self._note(f'[错误] {save_err}')
                messagebox.showerror('写入存档失败', save_err + '\n\n请关闭游戏/Steam云同步,或以管理员身份运行本工具后重试。')
                return
            self._invalidate()
            self._note(f'[完成] 已写入 {len(batch)} 个专精技能变更 备份:{os.path.basename(bak)}')

        self._mastery_save_async(save, 'mastery', done)

    def _mastery_save_async(self, save, tag, callback):
        """后台线程写档,避免 23MB 存档写入时主界面卡死。"""
        if getattr(self, '_mastery_saving', False):
            self._note('[信息] 正在写入存档,请稍候...')
            return False
        self._mastery_saving = True
        self._mastery_save_result = None
        self._mastery_save_callback = callback
        path = self.save_path.get()
        force = self.var_force.get()
        self._note(f'[信息] 正在写入存档({tag})...')
        self.root.update_idletasks()

        def worker():
            try:
                result = gct.try_save_and_backup(save, path, tag, force=force)
            except Exception as exc:
                result = (None, str(exc))
            self._mastery_save_result = result

        threading.Thread(target=worker, daemon=True).start()
        self.root.after(100, self._mastery_poll_save)
        return True

    def _mastery_poll_save(self):
        if getattr(self, '_mastery_save_result', None) is None:
            self.root.after(100, self._mastery_poll_save)
            return
        bak, err = self._mastery_save_result
        self._mastery_save_result = None
        self._mastery_saving = False
        callback = getattr(self, '_mastery_save_callback', None)
        self._mastery_save_callback = None
        if callback is not None:
            callback(bak, err)
        if err:
            # 写档失败:丢弃写入期间新排队的变更,避免反复弹窗
            if self._mastery_pending:
                self._mastery_discard_pending()
        elif self._mastery_pending:
            # 写入期间用户又点了别的节点,写完后自动继续下一批
            self._mastery_flush_pending()


    def _mastery_activate_selected(self):
        save = self._open()
        if save is None:
            return
        meta = self._selected_mastery_meta()
        if meta is None:
            return
        ch = self.var_mt_chara.get().strip()
        if not self._mastery_unit_belongs_to_chara(save, ch, meta['unit']):
            self._note('[错误] 当前选中行不属于下拉中的角色,请先重新读取专精技能'); return
        if int(meta['value'] or 0) > 0:
            return
        index = self._mastery_selected_index
        if index is None:
            return
        name = self._mastery_strip_style_prefix(meta.get('name')) or gct.mastery_effect_name(meta['effect'])
        if not self._mastery_queue_state(index, 1):
            return
        self._mastery_update_main_nodes()
        self._mastery_on_select()
        if self._mastery_saving:
            self._note(f'[信息] 已加入写入队列: {name}(当前写档完成后自动保存)')
        else:
            self._note(f'[信息] 已激活: {name}(后台写入中...)')
        self._mastery_flush_pending()

    def cmd_mastery_activate(self):
        self._mastery_activate_selected()

    def cmd_mastery_clear_all(self):
        save = self._open()
        if save is None:
            return
        ch = self.var_mt_chara.get().strip()
        rows = self._mastery_rows
        if not rows:
            self._note('[错误] 请先读取当前角色的专精技能'); return
        active = [(i, r) for i, r in enumerate(rows) if int(r['value'] or 0) > 0]
        if not active:
            self._note('[信息] 当前角色没有已激活的专精技能'); return
        if not messagebox.askyesno('确认清空', f'确定清空 {ch} 的全部专精技能吗?\n共 {len(active)} 个已激活节点。'):
            return
        for i, r in active:
            self._mastery_queue_state(i, 0, auto=True)
        self._mastery_update_main_nodes()
        self._mastery_on_select()
        self._note(f'[信息] 已加入清空队列: {ch} 共 {len(active)} 个专精技能')
        self._mastery_flush_pending()

    def _mastery_node_select(self, index):
        self._mastery_set_selected(index)

    def _mastery_canvas_double(self, _event=None):
        if not self.mastery_node_canvas.find_withtag("current"):
            return
        self._note('[提示] 单击未点亮节点即可激活;取消激活请选中后点“清空选中行”')

    def _mastery_on_mousewheel(self, event):
        # Windows 滚轮 delta 通常为 120 的倍数;向下滚为负
        if event.delta > 0:
            self.mastery_node_canvas.yview_scroll(-2, "units")
        else:
            self.mastery_node_canvas.yview_scroll(2, "units")

    def _mastery_refresh(self, save):
        if self._mastery_saving or self._mastery_pending:
            self._note('[信息] 正在写入/有待写入的专精技能,暂时不重新读取')
            return
        ch = self.var_mt_chara.get().strip()
        rows, err = gct.get_skillboard_rows(save, ch)
        if err:
            self._note(f'[错误] {err}'); return
        self._mastery_rows = rows
        self._mastery_selected_index = None
        self.mastery_tree.delete(*self.mastery_tree.get_children())
        for i, r in enumerate(rows):
            cat_name = gct.SKILLBOARD_CAT_NAMES[r['cat']] if 0 <= int(r['cat']) < 3 else str(r['cat'])
            disp_name = self._mastery_strip_style_prefix(r.get('name')) or gct.mastery_effect_name(r['effect'])
            self.mastery_tree.insert('', 'end', iid=str(i), values=(
                i + 1,
                self._mastery_grp_label(r['grp']),
                disp_name,
                gct.mastery_value_label(r['value']),
                cat_name,
                f'0x{r["effect"]:08X}' if r['effect'] not in (0, gct.EMPTY) else '',
                r['unit'],
            ))
        _, _gid = gct.find_chara(ch)
        disp = gct.chara_label(_gid) if _gid else ch
        self._note(f'[信息] {disp}: 专精技能记录 {len(rows)} 行')
        self._mastery_draw_nodes(rows)
        if rows:
            self._mastery_set_selected(0)
        else:
            self.var_mt_effect.set('')
            self.var_mt_value.set('1')

    def cmd_mastery_list(self):
        save = self._open()
        if save is None:
            return
        self._mastery_refresh(save)

    def cmd_mastery_apply(self):
        save = self._open()
        if save is None:
            return
        meta = self._selected_mastery_meta()
        if meta is None:
            self._note('[错误] 请先在专精/天赋表中选择一行'); return
        ch = self.var_mt_chara.get().strip()
        if not self._mastery_unit_belongs_to_chara(save, ch, meta['unit']):
            self._note('[错误] 当前选中行不属于下拉中的角色,请先重新「读取该角色专精/天赋」'); return
        if self._mastery_saving or self._mastery_pending:
            self._note('[信息] 正在写入或有待写入的专精技能,请稍后再用写入选中行'); return
        effect_q = self.var_mt_effect.get().strip()
        if not effect_q:
            effect_q = f'0x{meta["effect"]:08X}' if meta['effect'] not in (0, gct.EMPTY) else ''
        val_s = self.var_mt_value.get().strip()
        if not val_s:
            val_s = str(meta['value'])
        try:
            value = int(val_s)
        except ValueError:
            self._note(f'[错误] 状态/数值必须是整数: {val_s}'); return
        err = gct.set_mastery_row(save, ch, meta['unit'], effect_q, value)
        if err:
            self._note(f'[错误] {err}'); return
        bak, save_err = gct.try_save_and_backup(save, self.save_path.get(), 'mastery', force=self.var_force.get())
        if save_err:
            self._note(f'[错误] {save_err}'); return
        self._invalidate()
        self._note(f'[完成] 已写入专精/天赋 unit={meta["unit"]} (值={value}) 备份:{os.path.basename(bak)}')
        self.cmd_mastery_list()

    def cmd_mastery_toggle(self):
        save = self._open()
        if save is None:
            return
        meta = self._selected_mastery_meta()
        if meta is None:
            self._note('[错误] 请先在专精/天赋表中选择一行'); return
        ch = self.var_mt_chara.get().strip()
        if not self._mastery_unit_belongs_to_chara(save, ch, meta['unit']):
            self._note('[错误] 当前选中行不属于下拉中的角色,请先重新「读取该角色专精/天赋」'); return
        if meta['effect'] in (0, gct.EMPTY):
            self._note('[错误] 该行为空效果,不能直接点亮;请先写入效果'); return
        cur = int(meta['value'] or 0)
        new_val = 0 if cur > 0 else 1
        if not self._mastery_queue_state(self._mastery_selected_index, new_val):
            return
        self._mastery_update_main_nodes()
        self._mastery_on_select()
        self._mastery_flush_pending()

    def cmd_mastery_clear(self):
        save = self._open()
        if save is None:
            return
        meta = self._selected_mastery_meta()
        if meta is None:
            self._note('[错误] 请先在专精/天赋表中选择一行'); return
        ch = self.var_mt_chara.get().strip()
        if not self._mastery_unit_belongs_to_chara(save, ch, meta['unit']):
            self._note('[错误] 当前选中行不属于下拉中的角色,请先重新「读取该角色专精/天赋」'); return
        if not self._mastery_queue_state(self._mastery_selected_index, 0):
            return
        self._mastery_update_main_nodes()
        self._mastery_on_select()
        self._mastery_flush_pending()

    def cmd_mastery_enable_slot(self):
        save = self._open()
        if save is None:
            return
        ch = self.var_mt_chara.get().strip()
        err = gct.enable_sigil_slot_unlock(save, ch)
        if err:
            self._note(f'[错误] {err}'); return
        bak, save_err = gct.try_save_and_backup(save, self.save_path.get(), 'mastery', force=self.var_force.get())
        if save_err:
            self._note(f'[错误] {save_err}'); return
        self._invalidate()
        _, _gid = gct.find_chara(ch)
        disp = gct.chara_label(_gid) if _gid else ch
        self._note(f'[完成] {disp} 已点亮因子栏位解锁(13格) 备份:{os.path.basename(bak)}')
        self.cmd_mastery_list()

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
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'crab', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
        self._invalidate()
        self._note(f'[完成] 小钳蟹功能已写入 备份:{os.path.basename(bak)}')

    # ------------------------------------------------------------ 武器祝福
    def _tab_wrightstone(self, nb):
        t = ttk.Frame(nb, padding=8);nb.add(t, text=" 祝福 ")
        top = ttk.Frame(t)
        top.pack(fill="x", pady=(0,6))
        ttk.Label(top, text="祝福类型:").pack(side="left")
        ttk.Combobox(top, textvariable=self.var_wr_type, width=20, state="readonly", values=['%s (%s)' % (x[0], x[1]) for x in gct.WRIGHT_TYPES]).pack(side="left", padx=4)
        ttk.Button(top, text="刷新词条列表", command=self.cmd_wr_refresh).pack(side="left", padx=8)
        mid = ttk.LabelFrame(t, text="祝福配置(3 个词条 + 等级,等级 0-20)", padding=8);mid.pack(fill="x", pady=6)
        self._wr_trait_combos = []
        for i in range(3):
            row = ttk.Frame(mid);row.pack(fill="x", pady=2)
            ttk.Label(row, text=f"词条{i+1}:").pack(side="left")
            cb = ttk.Combobox(row, textvariable=self.var_wr_traits[i], width=22, state="normal");cb.pack(side="left", padx=4);self._wr_trait_combos.append(cb)
            ttk.Label(row, text="等级:").pack(side="left", padx=(8,0))
            ttk.Entry(row, textvariable=self.var_wr_levels[i], width=4).pack(side="left", padx=4)
        b = ttk.Frame(t);b.pack(fill="x", pady=(6,0))
        ttk.Button(b, text="生成祝福(写入存档)", style="Accent.TButton", command=lambda: self.cmd_wr_add(dry=False)).pack(side="left")
        ttk.Button(b, text="预览(不写入)", command=lambda: self.cmd_wr_add(dry=True)).pack(side="left", padx=8)
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
        """词条名 -> 哈希;失败返回 None。兼容“中文 (English)”“0xHASH (English)”格式。"""
        q = (q or '').strip()
        if not q:
            return None
        if q.lower().startswith('0x'):
            core, _ = gct._split_label(q)
            hex_part = core if core and core.lower().startswith('0x') else q
            try:
                return int(hex_part, 16) & 0xFFFFFFFF
            except ValueError:
                return None
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
        bak, _save_err = gct.try_save_and_backup(save, self.save_path.get(), 'wrightstone', force=self.var_force.get())
        if _save_err:
            self._note(f'[错误] {_save_err}')
            return
        self._invalidate()
        m2103 = self._vm(gct.WRIGHT_SERIAL_FIELD)
        self._note(f'[完成] 已生成 {wt[0]} (槽{slot}, 序列号={m2103.get(slot)}) 备份:{os.path.basename(bak)}')

    # ------------------------------------------------------------ 状态栏 / 关于 / 关闭
    def _build_statusbar(self):
        bar = ttk.Frame(self.root, padding=(8, 4))
        bar.pack(side="bottom", fill="x")
        self._status_bar = bar
        left = ttk.Label(bar, textvariable=self._status_save)
        right = ttk.Label(bar, textvariable=self._status_msg)
        left.configure(foreground=th.FG_DIM)
        right.configure(foreground=th.ACCENT)
        left.pack(side="left")
        right.pack(side="right")


    def _show_about(self):
        win = tk.Toplevel(self.root)
        win.title("关于")
        win.configure(bg=th.BG)
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)

        ttk.Label(win, text=APP_TITLE, font=th.font(13, bold=True), foreground=th.ACCENT).pack(anchor="w", padx=18, pady=4)
        ttk.Label(win, text="《碧蓝幻想:Relink》本地存档修改工具", foreground=th.FG).pack(anchor="w", padx=18, pady=4)
        ttk.Label(win, text="支持:物品 · 因子 · 角色配装 · 召唤石 · 配装方案 · 上限突破 · 小钳蟹 · 武器祝福", foreground=th.FG_DIM).pack(anchor="w", padx=18, pady=4)
        ttk.Label(win, text="写入前自动备份并重算校验和;修改前请完全退出游戏(含 Steam 云同步)", foreground=th.FG_DIM).pack(anchor="w", padx=18, pady=4)
        ttk.Label(win, text="快捷键:F5 刷新 · Ctrl+B 备份 · Ctrl+O 选择存档 · Ctrl+H 关于", foreground=th.FG_DIM).pack(anchor="w", padx=18, pady=4)
        ttk.Label(win, text="暗色主题 · UI 翻新", foreground=th.PURPLE).pack(anchor="w", padx=18, pady=4)

        ttk.Button(win, text="关闭", style="Accent.TButton", command=win.destroy).pack(pady=(6, 14))
        win.update_idletasks()
        w = win.winfo_reqwidth()
        h = win.winfo_reqheight()
        x = self.root.winfo_x() + (self.root.winfo_width() - w) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - h) // 2
        win.geometry(f"+{x}+{y}")


    def _on_close(self):
        if getattr(self, '_mastery_saving', False) or getattr(self, '_mastery_pending', None):
            messagebox.showinfo('正在写入', '存档正在写入,请等待写入完成后再关闭窗口。')
            return
        state = {"geometry": self.root.geometry()}
        path = os.path.join(gct.WRITE_DIR, "ui_state.json")
        try:
            with open(path, "w", encoding="utf-8") as fh:
                json.dump(state, fh, ensure_ascii=False)
        except Exception:
            pass
        finally:
            self.root.destroy()


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
    # --smoke 参数:自测模式,运行 N 秒后自动关闭(默认 2.5 秒),期间异常会冒泡
    if '--smoke' in sys.argv:
        idx = sys.argv.index('--smoke')
        secs = float(sys.argv[idx + 1]) if len(sys.argv) > idx + 1 else 2.5
        root.after(int(secs * 1000), root.destroy)
    root.mainloop()


if __name__ == '__main__':
    main()
