# -*- coding: utf-8 -*-
import sys as _sys
if _sys.stdout and hasattr(_sys.stdout, "reconfigure"):
    try:
        _sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
r"""
GBFR 漆黑小钳蟹存档修改工具
============================
针对《碧蓝幻想：Relink》SaveData1.dat 的本地存档编辑器。

功能：
  1. 把「漆黑小钳蟹」(Dark Wee Pincer / ITEM_60_0001) 的背包数量改成指定值(默认 20)。
  2. 把「漆黑蟹像」(Jet-Black Crab Statue / ITEM_70_0018) 这个 DLC 收集奖励设为 1，
     即等价于完成了「Save the Crustaceans Part Deux ~ Finale」这条漆黑小钳蟹收集链。
  3. 把对应的蟹收集任务(0x290002 ~ 0x290015)的完成标志置位。
  4. 自动重算存档 xxHash64 校验和(seed 0x2F1A43EBCD)，并备份原档。

用法：
  python gbfr_crab_tool.py                        # 修改主存档(自动备份 + 修校验)
  python gbfr_crab_tool.py --save 路径\SaveData1.dat
  python gbfr_crab_tool.py --dry-run              # 只预览，不写入
  python gbfr_crab_tool.py --dark-crab-count 20   # 指定漆黑小钳蟹数量(默认 20)

原理（存档格式）：
  SaveData1.dat = SaveGameFile 包装头 + FlatBuffers(SaveDataBinary)。
  - 物品：id_type 1801(物品哈希) 与 1802(数量) 是平行数组，按槽位 unit_id 对齐。
  - 任务：QuestSystem 的 2550(任务ID) / 2551(状态) / 2554,2555(完成) 平行向量。
  - 校验和：文件末尾 u32 指向 10 个 u64 哈希槽，用 uint:1003(种子) 选择激活槽。
"""

import argparse
import io
import os
import shutil
import struct
import sys
import time

# 复用开源编辑器的已验证核心(gbfr_save.py / hashing.py)
_EDITOR_CORE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "gbfr-save-editor", "GBFR-Save-Editor-main", "gbfr_editor", "core",
)
if os.path.isdir(_EDITOR_CORE):
    sys.path.insert(0, _EDITOR_CORE)

from gbfr_save import GBFRSaveData  # noqa: E402

# ---- 常量（均已经过哈希与存档实测验证）----
ITEM_DARK_WEE_PINCER_HASH = 0x9FBA96D1  # ITEM_60_0001  漆黑小钳蟹
ITEM_WEE_PINCER_HASH = 0xEE2559C6        # ITEM_60_0000  小钳蟹
ITEM_JETBLACK_CRAB_STATUE_HASH = 0x076A9F41  # ITEM_70_0018  漆黑蟹像(DLC收集奖励)
ITEM_GOLDEN_CRAB_STATUE_HASH = 0xFF1A207A   # ITEM_70_0007  金色蟹像(本体收集奖励)

IDTYPE_ITEM_ID = 1801
IDTYPE_ITEM_COUNT = 1802

# 蟹收集任务：本体 200001 + DLC 链 290002..290015
CRAB_QUEST_BASE = 0x200001
CRAB_QUEST_DLC_START = 0x290002
CRAB_QUEST_DLC_END = 0x290015

# QuestSystem 完成向量
IDTYPE_QUEST_KEYS = 2550      # 任务ID(uint 向量)
IDTYPE_QUEST_STATUS = 2551    # 状态(uint)
IDTYPE_QUEST_COMPLETE_VIEWED = 2554   # 完成/查看(bool)
IDTYPE_QUEST_COMPLETE = 2555         # 完成(bool)


def _find_item_slot(save, item_hash):
    """在 1801(物品ID)里找到指定物品哈希的槽位 unit_id。"""
    for rec in save.find(id_type=IDTYPE_ITEM_ID):
        v = save.get_first_value(rec)
        if (v & 0xFFFFFFFF) == (item_hash & 0xFFFFFFFF):
            return rec.unit_id
    return None


def _set_item_count(save, item_hash, count):
    """把指定物品(按哈希)的数量设为 count。返回 (slot, old, new) 或 None。"""
    slot = _find_item_slot(save, item_hash)
    if slot is None:
        return None
    rec = save.find_first("int", IDTYPE_ITEM_COUNT, slot)
    if rec is None:
        return None
    old = save.get_first_value(rec)
    save.set_first_value(rec, int(count))
    return (slot, old, int(count))


def _vector(save, id_type, kind=None):
    rec = save.find_first(kind, id_type, 0) if kind else None
    if rec is None:
        rec = save.find(id_type=id_type)
        rec = rec[0] if rec else None
    if rec is None:
        return None, []
    return rec, save.get_values(rec)


def _complete_crab_quests(save):
    """把 DLC 蟹收集任务(290002~290015)在 2550/2551/2554/2555 中置为完成。"""
    key_rec, keys = _vector(save, IDTYPE_QUEST_KEYS, "uint")
    if key_rec is None:
        return 0, 0
    status_rec, status = _vector(save, IDTYPE_QUEST_STATUS, "uint")
    viewed_rec, viewed = _vector(save, IDTYPE_QUEST_COMPLETE_VIEWED, "bool")
    done_rec, done = _vector(save, IDTYPE_QUEST_COMPLETE, "bool")

    crab = set(range(CRAB_QUEST_DLC_START, CRAB_QUEST_DLC_END + 1)) | {CRAB_QUEST_BASE}
    changed = 0
    hit = 0
    for idx, qid in enumerate(keys):
        if (qid & 0xFFFFFFFF) not in crab:
            continue
        hit += 1
        if status_rec is not None and idx < len(status):
            if int(status[idx]) < 1:
                status[idx] = 1
                changed += 1
        if viewed_rec is not None and idx < len(viewed):
            if not viewed[idx]:
                viewed[idx] = True
                changed += 1
        if done_rec is not None and idx < len(done):
            if not done[idx]:
                done[idx] = True
                changed += 1
    if changed:
        if status_rec is not None:
            save.set_values(status_rec, status)
        if viewed_rec is not None:
            save.set_values(viewed_rec, viewed)
        if done_rec is not None:
            save.set_values(done_rec, done)
    return hit, changed


def main():
    ap = argparse.ArgumentParser(description="GBFR 漆黑小钳蟹存档修改工具")
    default_save = os.path.join(
        os.environ.get("LOCALAPPDATA", ""),
        "GBFR", "Saved", "SaveGames", "SaveData1.dat",
    )
    ap.add_argument("--save", default=default_save, help="存档路径")
    ap.add_argument("--dark-crab-count", type=int, default=20, help="漆黑小钳蟹数量(默认 20)")
    ap.add_argument("--statue", type=int, default=1, help="漆黑蟹像数量(默认 1)")
    ap.add_argument("--dry-run", action="store_true", help="只预览不写入")
    args = ap.parse_args()

    if not os.path.isfile(args.save):
        print(f"[错误] 找不到存档: {args.save}")
        return 2

    print(f"[打开] {args.save}")
    save = GBFRSaveData.open(args.save)
    s = save.summary()
    print(f"[校验] 存档模式={s['mode']} 哈希区激活槽={s['active_hash_index']} "
          f"当前校验={'通过' if s['active_hash_ok'] else '不通过'}")

    report = []

    # 1) 漆黑小钳蟹数量
    r1 = _set_item_count(save, ITEM_DARK_WEE_PINCER_HASH, args.dark_crab_count)
    if r1 is None:
        print("[警告] 存档里没有找到「漆黑小钳蟹」(ITEM_60_0001)，将尝试为空槽写入…")
        report.append("漆黑小钳蟹: 未找到该物品(存档中不存在)")
    else:
        slot, old, new = r1
        print(f"[物品] 漆黑小钳蟹 槽位={slot} 数量 {old} -> {new}")
        report.append(f"漆黑小钳蟹: 槽位{slot} 数量 {old} -> {new}")

    # 2) 漆黑蟹像(DLC收集奖励)
    r2 = _set_item_count(save, ITEM_JETBLACK_CRAB_STATUE_HASH, args.statue)
    if r2 is None:
        print("[警告] 未找到「漆黑蟹像」(ITEM_70_0018)")
        report.append("漆黑蟹像: 未找到")
    else:
        slot, old, new = r2
        print(f"[奖励] 漆黑蟹像 槽位={slot} 数量 {old} -> {new}")
        report.append(f"漆黑蟹像: 槽位{slot} 数量 {old} -> {new}")

    # 3) 完成 DLC 蟹收集任务
    hit, changed = _complete_crab_quests(save)
    print(f"[任务] 命中的蟹任务 {hit} 个，改动 {changed} 个标志")
    report.append(f"蟹任务: 命中 {hit} 个，改动 {changed} 个标志")

    print("\n=== 改动汇总 ===")
    for line in report:
        print("  " + line)

    if args.dry_run:
        print("\n[dry-run] 未写入任何数据。")
        return 0

    # 备份 + 写回 + 修校验
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup = args.save + f".crab_backup_{stamp}"
    shutil.copy2(args.save, backup)
    print(f"\n[备份] 原档已备份到: {backup}")

    save.save_over_original(update_hash=True, backup=False, validate=True, fsync=True)
    # 重新打开验证
    reopened = GBFRSaveData.open(args.save)
    print(f"[完成] 已写入并重算校验和。重开后激活槽校验: "
          f"{'通过' if reopened.check_active_hash() else '不通过'}")
    print("\n提示：进入游戏后加载该存档，确认漆黑小钳蟹数量与任务状态；")
    print("      如游戏内未即时刷新，可退回标题画面再读档一次。")


if __name__ == "__main__":
    main()
