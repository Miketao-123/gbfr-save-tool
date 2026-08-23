# -*- coding: utf-8 -*-
"""GBFR 存档修改器暗色主题模块。"""
import tkinter as tk
from tkinter import ttk

BG = "#0d1b2c"
BG_PANEL = "#1b2636"
BG_INPUT = "#0f1d2e"
BG_TEXT = "#101418"
FG = "#e8ecf1"
FG_DIM = "#8b98a9"
FG_FAINT = "#5c6b7f"
ACCENT = "#67e8f9"
ACCENT_DARK = "#22b8d4"
GREEN = "#4ade80"
RED = "#f87171"
AMBER = "#fbbf24"
PURPLE = "#a5b4fc"
BORDER = "#2e4057"
BORDER_LT = "#3b5371"
FONT_FAMILY = "Microsoft YaHei UI"
FONT_FAMILY_MONO = "Consolas"


def font(size=10, bold=False):
    return (FONT_FAMILY, size, 'bold' if bold else 'normal')


def mono_font(size=10):
    return (FONT_FAMILY_MONO, size)


def _style_base(st):
    st.configure('.', font=(FONT_FAMILY, 10), background=BG, foreground=FG)

    st.configure('TFrame', background=BG)

    st.configure('TLabel', background=BG, foreground=FG)

    st.configure(
        'TButton',
        background=BG_PANEL,
        foreground=FG,
        bordercolor=BORDER,
        lightcolor=BORDER_LT,
        darkcolor=BORDER,
        focuscolor=ACCENT_DARK,
        padding=(12, 5),
    )
    st.map(
        'TButton',
        background=[('pressed', ACCENT_DARK), ('active', '#24364a')],
        foreground=[('disabled', FG_FAINT)],
    )

    st.configure(
        'Accent.TButton',
        background=ACCENT,
        foreground='#0b1220',
        bordercolor=ACCENT,
        focuscolor=ACCENT,
    )
    st.map(
        'Accent.TButton',
        background=[('pressed', '#3dd5f5'), ('active', '#7eeefc')],
    )

    st.configure(
        'Green.TButton',
        background=GREEN,
        foreground='#0b1220',
        bordercolor=GREEN,
    )

    st.configure(
        'Danger.TButton',
        background=RED,
        foreground='#0b1220',
        bordercolor=RED,
    )

    st.configure(
        'TEntry',
        fieldbackground=BG_INPUT,
        foreground=FG,
        insertcolor=ACCENT,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
        selectbackground=ACCENT_DARK,
        selectforeground=FG,
    )
    st.map(
        'TEntry',
        fieldbackground=[('readonly', BG_INPUT)],
        foreground=[('disabled', FG_FAINT)],
        bordercolor=[('focus', ACCENT)],
    )

    st.configure(
        'TCombobox',
        fieldbackground=BG_INPUT,
        background=BG_PANEL,
        foreground=FG,
        arrowcolor=ACCENT,
        bordercolor=BORDER,
        selectbackground=ACCENT_DARK,
        selectforeground=FG,
    )
    st.map(
        'TCombobox',
        fieldbackground=[('readonly', BG_INPUT)],
        foreground=[('disabled', FG_FAINT)],
        bordercolor=[('focus', ACCENT)],
    )

    st.configure('TCheckbutton', background=BG, foreground=FG, focuscolor=BG)
    st.map('TCheckbutton', background=[('active', BG)])

    st.configure(
        'TLabelframe',
        background=BG_PANEL,
        bordercolor=BORDER,
        lightcolor=BORDER,
        darkcolor=BORDER,
    )

    st.configure('TLabelframe.Label', background=BG_PANEL, foreground=ACCENT)


def _style_options(root):
    root.option_add('*TCombobox*Listbox.background', BG_INPUT)
    root.option_add('*TCombobox*Listbox.foreground', FG)
    root.option_add('*TCombobox*Listbox.selectBackground', '#0e3a4a')
    root.option_add('*TCombobox*Listbox.selectForeground', ACCENT)
    root.option_add('*TCombobox*Listbox.font', (FONT_FAMILY, 10))

    root.option_add('*Menu.background', BG_PANEL)
    root.option_add('*Menu.foreground', FG)
    root.option_add('*Menu.activeBackground', ACCENT_DARK)
    root.option_add('*Menu.activeForeground', '#0b1220')
    root.option_add('*Menu.borderWidth', 0)


def apply_theme(root):
    st = ttk.Style()
    st.theme_use('clam')
    _style_base(st)
    _style_advanced(st)
    _style_options(root)
    root.configure(bg=BG)


def _style_advanced(st):
    st.configure(
        'TNotebook',
        background=BG,
        borderwidth=0,
    )
    st.map('TNotebook', background=[('selected', BG_PANEL)])

    st.configure(
        'TNotebook.Tab',
        background='#182636',
        foreground=FG_DIM,
        padding=(16, 7),
        borderwidth=0,
        lightcolor=BG,
        darkcolor=BG,
    )
    st.map(
        'TNotebook.Tab',
        background=[('selected', BG_PANEL)],
        foreground=[('selected', ACCENT)],
    )

    for name in ('Vertical.TScrollbar', 'Horizontal.TScrollbar'):
        st.configure(
            name,
            background='#33415c',
            troughcolor=BG,
            bordercolor=BG,
            arrowcolor=ACCENT,
            lightcolor='#33415c',
            darkcolor='#33415c',
        )
        st.map(
            name,
            background=[('pressed', ACCENT_DARK), ('active', '#3e5070')],
        )

    st.configure(
        'TProgressbar',
        background=ACCENT,
        troughcolor=BG_PANEL,
        bordercolor=BG_PANEL,
    )
def configure_tags(text_widget):
    colors = {'err': RED, 'warn': AMBER, 'done': GREEN, 'preview': PURPLE, 'info': ACCENT}
    existing = set(text_widget.tag_names())
    for name, color in colors.items():
        if name not in existing:
            text_widget.tag_configure(name, foreground=color)


def emit_line(text_widget, line):
    configure_tags(text_widget)

    if '[错误]' in line:
        tag = 'err'
    elif '[警告]' in line:
        tag = 'warn'
    elif '[完成]' in line:
        tag = 'done'
    elif '[预览]' in line:
        tag = 'preview'
    elif any(marker in line for marker in ('[信息]', '[物品]', '[任务]', '[奖励]')):
        tag = 'info'
    else:
        tag = None

    if tag is not None:
        text_widget.insert('end', line, tag)
    else:
        text_widget.insert('end', line)
    text_widget.see('end')


def make_icon():
    img = tk.PhotoImage(width=64, height=64)

    top_color = '#a5f3fc'
    mid_color = ACCENT
    dark_color = ACCENT_DARK
    bottom_color = '#155e75'
    edge_color = '#3dd5f5'

    for y in range(64):
        dy = abs(y - 32)

        if y < 32:
            base_color = top_color
        elif y <= 44:
            base_color = mid_color
        elif y <= 52:
            base_color = dark_color
        else:
            base_color = bottom_color

        for x in range(64):
            dx = abs(x - 32)
            dist = (dx + dy) / 26.0

            if dist > 1.0:
                continue

            color = edge_color if x > 32 and dist > 0.75 else base_color
            img.put(color, to=(x, y, x + 1, y + 1))

    return img