# -*- coding: utf-8 -*-
import sys as _sys
if _sys.stdout and hasattr(_sys.stdout, "reconfigure"):
    try:
        _sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
r"""
GBFR 漆黑小钳蟹因子(可怕的漆黑钳蟹因子)注入工具
================================================
在存档 GemManager 里找一个空因子槽,写入：
  因子:  GEEN_301_00 「可怕的漆黑钳蟹因子」(Dread Black Pincer Crab Sigil)
         gem 哈希 0x49434696
  主词条: SKILL_301_00 「可怕的漆黑钳蟹因子」,哈希 0xBF78FBFC
  等级:  20 (词条满级,对应 20 只漆黑小钳蟹收集)
并自动重算 xxHash64 校验和 + 备份。

用法：
  python gbfr_sigil_tool.py [--save 路径] [--level 20] [--plus] [--dry-run]
  --plus  额外注入 + 版(GEEN_301_10,副词条为钳蟹的报恩)
"""

import argparse
import os
import shutil
import sys
import time

_EDITOR_CORE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "gbfr-save-editor", "GBFR-Save-Editor-main", "gbfr_editor", "core",
)
if os.path.isdir(_EDITOR_CORE):
    sys.path.insert(0, _EDITOR_CORE)

from gbfr_save import GBFRSaveData  # noqa: E402

EMPTY = 0x887AE0B0

GEM_DREAD = 0x49434696      # GEEN_301_00 可怕的漆黑钳蟹因子
GEM_DREAD_PLUS = 0x66CB28BA  # GEEN_301_10 可怕的漆黑钳蟹因子+
SKILL_DREAD = 0xBF78FBFC    # SKILL_301_00 可怕的漆黑钳蟹因子
SKILL_CRABVESTMENT = 0x1B0D9897  # SKILL_141_00 钳蟹的报恩(+版副词条)

ID_2701 = 2701   # GEMDATA_MAX_SLOT_ID
ID_2702 = 2702   # GEMDATA_SLOT_IDS
ID_2703 = 2703   # GEMDATA_GEM_ID
ID_2704 = 2704   # GEMDATA_SKILL_1_LEVEL
ID_2706 = 2706   # GEMDATA_WORN_BY
ID_2707 = 2707   # GEMDATA_FLAGS
ID_1701 = 1701   # EQUIPMENT_TRAIT_ID
ID_1702 = 1702   # EQUIPMENT_TRAIT_LEVEL

GEM_SLOT_BASE = 30000
TRAIT_REC_BASE = 120000000


def find_empty_slot(save):
    m2703 = {r.unit_id: save.get_first_value(r) for r in save.find(id_type=ID_2703)}
    empty = [s for s, g in m2703.items() if (g & 0xFFFFFFFF) == EMPTY]
    if not empty:
        return None
    # prefer the lowest empty slot after the last used slot
    used = [s for s, g in m2703.items() if (g & 0xFFFFFFFF) != EMPTY]
    last_used = max(used) if used else GEM_SLOT_BASE - 1
    candidates = [s for s in empty if s > last_used]
    return min(candidates) if candidates else min(empty)


def main():
    ap = argparse.ArgumentParser(description="GBFR 漆黑小钳蟹因子注入工具")
    default_save = os.path.join(os.environ.get("LOCALAPPDATA", ""),
                                "GBFR", "Saved", "SaveGames", "SaveData1.dat")
    ap.add_argument("--save", default=default_save)
    ap.add_argument("--level", type=int, default=20, help="因子/词条等级(默认 20,最大 20)")
    ap.add_argument("--plus", action="store_true", help="注入 + 版(带副词条:钳蟹的报恩)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    if not os.path.isfile(args.save):
        print(f"[错误] 找不到存档: {args.save}")
        return 2
    print(f"[打开] {args.save}")
    save = GBFRSaveData.open(args.save)
    s = save.summary()
    print(f"[校验] 模式={s['mode']} 激活哈希槽={s['active_hash_index']} 当前校验={'通过' if s['active_hash_ok'] else '不通过'}")

    slot = find_empty_slot(save)
    if slot is None:
        print("[错误] 没有空因子槽")
        return 1
    idx = slot - GEM_SLOT_BASE

    gem = GEM_DREAD_PLUS if args.plus else GEM_DREAD
    trait2 = SKILL_CRABVESTMENT if args.plus else EMPTY
    gem_name = "可怕的漆黑钳蟹因子＋" if args.plus else "可怕的漆黑钳蟹因子"

    # current state
    m2701 = {r.unit_id: save.get_first_value(r) for r in save.find(id_type=ID_2701)}
    max_count = int(m2701.get(0, 0))
    new_count = max_count + 1

    print(f"[因子] 槽位 {slot} <- {gem_name} (gem=0x{gem:08X}, 主词条=0x{SKILL_DREAD:08X}, "
          f"副词条={'0x%08X' % trait2 if trait2 != EMPTY else '无'}, 等级={args.level})")
    print(f"[计数] 2701 最大槽计数 {max_count} -> {new_count}")

    if args.level < 1 or args.level > 20:
        print(f"[警告] 等级 {args.level} 超出该词条的 1..20 范围,仍将写入(游戏可能自行校正)")

    if args.dry_run:
        print("\n[dry-run] 未写入。")
        return 0

    # --- write ---
    def set_first(idt, unit, val):
        rec = save.find_first("uint" if not isinstance(val, int) else "int", idt, unit)
        if rec is None:
            # try the other kind
            for kind in ("uint", "int"):
                rec = save.find_first(kind, idt, unit)
                if rec is not None:
                    break
        if rec is None:
            raise RuntimeError(f"缺少 id_type={idt} unit={unit} 的记录")
        save.set_first_value(rec, val)

    # 2701 max slot count
    set_first(ID_2701, 0, new_count)
    # slot id (2702)
    set_first(ID_2702, slot, new_count)
    # gem id (2703)
    set_first(ID_2703, slot, gem)
    # level (2704)
    set_first(ID_2704, slot, args.level)
    # worn by (2706) = not equipped
    set_first(ID_2706, slot, EMPTY)
    # flags (2707) = 0x2
    set_first(ID_2707, slot, 0x2)
    # trait1 (1701) + level (1702)
    set_first(ID_1701, TRAIT_REC_BASE + idx * 100, SKILL_DREAD)
    set_first(ID_1702, TRAIT_REC_BASE + idx * 100, args.level)
    # trait2 (1701+1) + level (1702+1)
    set_first(ID_1701, TRAIT_REC_BASE + idx * 100 + 1, trait2)
    set_first(ID_1702, TRAIT_REC_BASE + idx * 100 + 1, args.level)

    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup = args.save + f".sigil_backup_{stamp}"
    shutil.copy2(args.save, backup)
    print(f"[备份] {backup}")

    save.save_over_original(update_hash=True, backup=False, validate=True, fsync=True)
    reopened = GBFRSaveData.open(args.save)
    print(f"[完成] 已写入并重算校验和。重开校验: {'通过' if reopened.check_active_hash() else '不通过'}")
    # verify
    m2703 = {r.unit_id: save.get_first_value(r) for r in reopened.find(id_type=ID_2703)}
    print(f"[验证] 槽位 {slot} gem=0x{m2703.get(slot,0):08X} (期望 0x{gem:08X})")
    print("\n提示:进游戏后该因子会出现在因子列表(背包)。词条等级受漆黑小钳蟹收集数影响;")


if __name__ == "__main__":
    main()
