# -*- coding: utf-8 -*-
"""GUI 交互回归:切页 + 只读命令 + 关于对话框,全部在真实存档上执行。"""
import sys
import os
import traceback

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'save_tool'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
import gbfr_gui

errors = []


def main():
    root = tk.Tk()
    try:
        app = gbfr_gui.App(root)
    except Exception:
        traceback.print_exc()
        errors.append('App init failed')
        root.destroy()
        return 1

    def step():
        try:
            root.update()
            # 等初始 refresh 完成
            root.after(4000, run_checks)
        except Exception:
            traceback.print_exc()
            errors.append('update failed')
            root.destroy()

    def run_checks():
        try:
            nb = app.nb
            names = [nb.tab(t, 'text') for t in nb.tabs()]
            print('TABS:', names)
            for i in range(len(nb.tabs())):
                nb.select(i)
                root.update()
                print('switched to tab', i, names[i])
            # 回到物品页
            nb.select(0)
            root.update()

            app.cmd_items_list()
            app.cmd_sigils_list()
            app.cmd_chars_list()
            app.cmd_summons_list()
            app.cmd_ld_list()
            app.cmd_wr_refresh()
            print('read-only commands OK')

            # 关于对话框
            app._show_about()
            root.update()
            print('about dialog OK')

            # 状态栏
            print('status_save:', app._status_save.get())
            print('status_msg:', app._status_msg.get())
            print('items_out lines:', int(app.items_out.index('end-1c').split('.')[0]))
            print('log lines:', int(app.log.index('end-1c').split('.')[0]))
        except Exception:
            traceback.print_exc()
            errors.append('checks failed')
        finally:
            root.after(1500, root.destroy)

    root.after(200, step)
    root.mainloop()
    print('ERRORS:', errors if errors else 'NONE')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main())
