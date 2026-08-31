# -*- coding: utf-8 -*-
import sys as _sys
if _sys.stdout and hasattr(_sys.stdout, "reconfigure"):
    try:
        _sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
r"""
GBFR 简易作弊器 (本地存档修改)  v1.3
====================================
功能：
  1) 物品数量修改        : items set <名称/ID> <数量>
  2) 定向生成合法因子    : sigils add <名称/ID> [--level N] [--secondary 词条] [--equip PLxxxx]
  3) 角色因子配装        : chars sigils/equip/unequip/clear
  4) 召唤石(DLC 2.0 背包) : summons list/set/add/equip/catalog/traits/subparams (真实名称显示)
  5) 配装方案(工具侧)    : loadout save/restore (保存/恢复某角色的因子配装)

用法示例：
  python gbfr_cheat_tool.py items list 漆黑
  python gbfr_cheat_tool.py items set 漆黑小钳蟹 99
  python gbfr_cheat_tool.py sigils list 蟹
  python gbfr_cheat_tool.py sigils add 可怕的漆黑钳蟹因子 --level 20
  python gbfr_cheat_tool.py sigils add "Glass Cannon V+" --secondary 攻击力 --equip PL0000
  python gbfr_cheat_tool.py chars sigils PL0000
  python gbfr_cheat_tool.py summons list
  python gbfr_cheat_tool.py summons catalog 路西法
  python gbfr_cheat_tool.py summons add 路西法 --main 攻击力 --sub "攻击力（高·最高3000）" --main-level 15 --sub-level 9 --rank 3
  python gbfr_cheat_tool.py loadout save 我的配装 PL0000
  python gbfr_cheat_tool.py loadout restore 我的配装
"""
import argparse, json, os, shutil, sys, time

EMPTY = 0x887AE0B0
DEFAULT_SAVE = os.path.join(os.environ.get('LOCALAPPDATA', ''), 'GBFR', 'Saved', 'SaveGames', 'SaveData1.dat')

# ---- 资源路径:兼容源码运行与 PyInstaller 打包(frozen) ----
if getattr(sys, 'frozen', False):
    # PyInstaller 打包:数据文件在 _MEIPASS 只读目录
    RES_DIR = sys._MEIPASS
    # 可写目录:存档同目录的 _loadouts(或用户目录兜底)
    _save_dir = os.path.dirname(DEFAULT_SAVE) if DEFAULT_SAVE else ''
    WRITE_DIR = os.path.join(_save_dir, '_loadouts') if os.path.isdir(_save_dir) else \
        os.path.join(os.path.expanduser('~'), 'GBFR_SaveTool_loadouts')
else:
    RES_DIR = os.path.dirname(os.path.abspath(__file__))
    WRITE_DIR = os.path.join(RES_DIR, 'loadouts')

BASE = RES_DIR
CORE = os.path.join(RES_DIR, 'gbfr-save-editor', 'GBFR-Save-Editor-main', 'gbfr_editor', 'core')
if os.path.isdir(CORE):
    sys.path.insert(0, CORE)
from gbfr_save import GBFRSaveData  # noqa: E402
from hashing import gbfr_hash       # noqa: E402

ID_ITEM_ID, ID_ITEM_COUNT = 1801, 1802
ID_2701, ID_2702, ID_2703, ID_2704, ID_2706, ID_2707 = 2701, 2702, 2703, 2704, 2706, 2707
ID_1701, ID_1702 = 1701, 1702
GEM_SLOT_BASE = 30000
TRAIT_REC_BASE = 120000000
# summon vectors (旧版 3101-3115, 保留只读展示)
ID_SUM_CHARA, ID_SUM_LEVEL, ID_SUM_TYPE = 3101, 3102, 3113
SUMMON_UNIT_BASE = 10100

# ---- 召唤石 (DLC 2.0 背包系统, id_type 布局与 GBFR PE Patch Tool 一致) ----
#   1451 uint[4] @0       已装备的 4 个召唤石 (SlotID; 0 = 空槽)
#   1452 uint   @0..299   登记目录: 已知召唤石种类哈希 (300 行)
#   1453 uint   @0..299   登记标志 0/1 (对应 1452 行)
#   1454 uint   @0        最大 SlotID
#   1455 uint   @0        召唤系统解锁 0/1
#   1456 uint   @0..999   SlotID (0 = 空记录)
#   1457 uint   @0..999   种类哈希 (0x887AE0B0 = 空)
#   1458 uint[2] @0..999  [主加护哈希, 副词条哈希]
#   1459 int[2]  @0..999  [主加护等级, 副词条档位]
#   1460 uint   @0..999   阶级 0-3
ID_SUM_EQUIPPED, ID_SUM_CATALOG, ID_SUM_REGISTERED = 1451, 1452, 1453
ID_SUM_MAXSLOT, ID_SUM_UNLOCKED = 1454, 1455
ID_SUM_SLOT, ID_SUM_TYPE2, ID_SUM_TRAITS, ID_SUM_LEVELS, ID_SUM_RANK = 1456, 1457, 1458, 1459, 1460
SUMMON_CAPACITY = 1000
SUMMON_CATALOG_ROWS = 300
SUMMON_EMPTY_LEVEL = 0xFFFFFFFF   # 空记录的等级占位
SUMMON_MAX_MAIN_LEVEL = 15        # 2.0.2 summon_curve 主加护等级上限
SUMMON_MAX_RANK = 3               # 阶级 0-3

# ------- catalogs -------
def _load(path):
    with open(os.path.join(BASE, path), encoding='utf-8') as f:
        return json.load(f)

CAT = _load('catalog.json')
GEMCAT = _load('catalog_gem.json')
CHARSCAT = _load('catalog_chars.json')
SIGILS_FULL = _load('catalog_sigils_full.json') if os.path.exists(os.path.join(BASE, 'catalog_sigils_full.json')) else {}
# 游戏权威合法性数据(由 system/table 提取,见 gem_legality.json)
LEGAL = _load('gem_legality.json') if os.path.exists(os.path.join(BASE, 'gem_legality.json')) else None
# 角色名表(PLxxxx -> {cn, en},来源:游戏本体 system/table/text/{cs,en}/text_chara.msg)
CHAR_NAMES = _load('chara_names.json') if os.path.exists(os.path.join(BASE, 'chara_names.json')) else {}


def chara_name(pl):
    """PLxxxx -> 中文名(优先)或英文名;没有名字时返回 PL 代码本身。"""
    e = CHAR_NAMES.get(pl)
    if e:
        return e.get('cn') or e.get('en') or pl
    return pl


def chara_label(pl):
    """显示用标签: 卡塔莉娜 (Katalina)  [PL0200];无名字时仅 PL 代码。"""
    e = CHAR_NAMES.get(pl)
    if not e:
        return pl
    cn = e.get('cn'); en = e.get('en')
    if cn and en:
        return '%s (%s)' % (cn, en)
    return cn or en or pl


def chara_gid_by_hash(h):
    """角色哈希(int) -> PL代码;找不到返回 None。"""
    h = int(h) & 0xFFFFFFFF
    for k, gid in CHARSCAT.items():
        if int(k) & 0xFFFFFFFF == h:
            return gid
    return None


def chara_label_by_hash(h):
    """角色哈希(int) -> 显示名;找不到时显示 0x 哈希。"""
    gid = chara_gid_by_hash(h)
    return chara_label(gid) if gid else f'0x{int(h) & 0xFFFFFFFF:08X}'

# ---- 召唤石目录 (catalog_summon.json, 逆向自 GBFR PE Patch Tool) ----
SUMCAT = _load('catalog_summon.json') if os.path.exists(os.path.join(BASE, 'catalog_summon.json')) else {}
SUMCAT_TYPES = SUMCAT.get('types', {})          # str(hash) -> {cn,en,baseName,code,cost,typeName,tier,mode,...}
SUMCAT_MAIN = SUMCAT.get('main_traits', {})     # str(hash) -> {cn,en,maxLevel}
SUMCAT_SUB = SUMCAT.get('sub_params', {})       # str(hash) -> {cn,maxLevel,isPercent,values}


def _sum_key(h):
    return str(int(h) & 0xFFFFFFFF)


def summon_type_name(h, with_en=False):
    """召唤石种类哈希 -> 中文名(可带英文)。未知时返回 0x 哈希。"""
    e = SUMCAT_TYPES.get(_sum_key(h))
    if not e:
        return f'0x{int(h) & 0xFFFFFFFF:08X}'
    cn = e.get('cn') or e.get('en') or f'0x{int(h) & 0xFFFFFFFF:08X}'
    if with_en and e.get('en'):
        return f'{cn} ({e["en"]})'
    return cn


def summon_trait_name(h, with_en=False):
    """主加护(技能)哈希 -> 中文名(可带英文)。未知时返回 0x 哈希。"""
    e = SUMCAT_MAIN.get(_sum_key(h))
    if not e:
        return f'0x{int(h) & 0xFFFFFFFF:08X}'
    cn = e.get('cn') or e.get('en') or f'0x{int(h) & 0xFFFFFFFF:08X}'
    if with_en and e.get('en'):
        return f'{cn} ({e["en"]})'
    return cn


def summon_sub_name(h):
    """副词条哈希 -> 中文名。未知时返回 0x 哈希。"""
    e = SUMCAT_SUB.get(_sum_key(h))
    if not e:
        return f'0x{int(h) & 0xFFFFFFFF:08X}'
    return e.get('cn') or f'0x{int(h) & 0xFFFFFFFF:08X}'


def summon_main_max_level(h):
    """主加护等级上限(目录 maxLevel, 再被 2.0.2 曲线上限 15 钳制)。"""
    e = SUMCAT_MAIN.get(_sum_key(h))
    ml = int(e.get('maxLevel', 15) or 15) if e else 15
    return max(0, min(ml, SUMMON_MAX_MAIN_LEVEL))


def summon_sub_max_level(h):
    """副词条档位上限(目录 maxLevel)。"""
    e = SUMCAT_SUB.get(_sum_key(h))
    return max(0, int(e.get('maxLevel', 9) or 9)) if e else 9


def _extract_hash(q0):
    """从输入中提取内嵌 0x 哈希(如 '路西法 · 传说 · 特殊 (Lucilius) [0x6E5968FC]')。"""
    import re
    m = re.search(r'0[xX][0-9A-Fa-f]{8}', q0)
    return int(m.group(0), 16) & 0xFFFFFFFF if m else None


def _split_label(q0):
    """把 '中文 (English)' 拆成 (中文, English);带 [0x...] 时先去掉。"""
    import re
    s = re.sub(r'\s*\[0[xX][0-9A-Fa-f]{8}\]', '', q0).strip()
    if ' (' in s and s.endswith(')'):
        i = s.index(' (')
        return s[:i].strip(), s[i + 2:-1].strip()
    return s, None


def summon_find_type(q):
    """按名称(中文/英文/baseName)/code/0x哈希 解析召唤石种类 -> 哈希。失败返回 None。"""
    q0 = (q or '').strip()
    if not q0:
        return None
    hx = _extract_hash(q0)
    if hx is not None:
        return hx if _sum_key(hx) in SUMCAT_TYPES else None
    if q0.lower().startswith('0x'):
        return int(q0, 16) & 0xFFFFFFFF
    core, en_part = _split_label(q0)
    ql = q0.lower()
    core_l = (core or '').lower()
    en_l = (en_part or '').lower()
    hits = []
    for hk, e in SUMCAT_TYPES.items():
        cn = (e.get('cn') or '').lower()
        en = (e.get('en') or '').lower()
        bn = (e.get('baseName') or '').lower()
        code = (e.get('code') or '').lower()
        if cn == ql or en == ql or (core_l and cn == core_l) or (en_l and en == en_l) or (core_l and bn == core_l) or ql == code:
            return int(hk) & 0xFFFFFFFF
        if (core_l and cn and core_l in cn) or (core_l and bn and core_l in bn):
            hits.append((int(hk) & 0xFFFFFFFF, e))
    if not hits:
        return None
    def score(item):
        h, e = item
        cn = (e.get('cn') or '').lower(); bn = (e.get('baseName') or '').lower()
        if cn == core_l or bn == core_l:
            return 0
        if bn and core_l in bn:
            return 1
        return 2
    return min(hits, key=score)[0]


def summon_find_main(q):
    """按名称/0x哈希 解析主加护 -> 哈希。失败返回 None。"""
    q0 = (q or '').strip()
    if not q0:
        return None
    hx = _extract_hash(q0)
    if hx is not None:
        return hx if _sum_key(hx) in SUMCAT_MAIN else None
    if q0.lower().startswith('0x'):
        return int(q0, 16) & 0xFFFFFFFF
    core, en_part = _split_label(q0)
    ql = q0.lower()
    core_l = (core or '').lower()
    en_l = (en_part or '').lower()
    best = None
    best_len = None
    for hk, e in SUMCAT_MAIN.items():
        cn = (e.get('cn') or '').lower()
        en = (e.get('en') or '').lower()
        if cn == ql or (core_l and cn == core_l) or (en_l and en == en_l):
            return int(hk) & 0xFFFFFFFF
        if core_l and cn and (core_l in cn or cn in core_l):
            if best_len is None or len(cn) < best_len:
                best = int(hk) & 0xFFFFFFFF
                best_len = len(cn)
    return best


def summon_find_sub(q):
    """按名称/0x哈希 解析副词条 -> 哈希。失败返回 None。"""
    q0 = (q or '').strip()
    if not q0:
        return None
    hx = _extract_hash(q0)
    if hx is not None:
        return hx if _sum_key(hx) in SUMCAT_SUB else None
    if q0.lower().startswith('0x'):
        return int(q0, 16) & 0xFFFFFFFF
    core, _ = _split_label(q0)
    ql = q0.lower()
    core_l = (core or '').lower()
    best = None
    best_len = None
    for hk, e in SUMCAT_SUB.items():
        cn = (e.get('cn') or '').lower()
        if cn == ql or (core_l and cn == core_l):
            return int(hk) & 0xFFFFFFFF
        if core_l and (core_l in cn or cn in core_l):
            if best_len is None or len(cn) < best_len:
                best = int(hk) & 0xFFFFFFFF
                best_len = len(cn)
    return best


def summon_empty_state():
    """空记录状态(与 PE Patch Tool 判定一致)。"""
    return (EMPTY, EMPTY, EMPTY, SUMMON_EMPTY_LEVEL, SUMMON_EMPTY_LEVEL, 0)


def summon_maps(save):
    """一次性构建召唤石背包映射(5 个 id_type),避免逐 unit 全表扫描。"""
    m1456 = vm(save, ID_SUM_SLOT)
    m1457 = vm(save, ID_SUM_TYPE2)
    m1458 = {r.unit_id: list(save.get_values(r)) for r in save.find(id_type=ID_SUM_TRAITS)}
    m1459 = {r.unit_id: list(save.get_values(r)) for r in save.find(id_type=ID_SUM_LEVELS)}
    m1460 = vm(save, ID_SUM_RANK)
    return m1456, m1457, m1458, m1459, m1460


def summon_record_from_maps(maps, unit):
    """从预构建映射读 unit 的记录;空记录返回 None。"""
    m1456, m1457, m1458, m1459, m1460 = maps
    slot = int(m1456.get(unit, 0) or 0) & 0xFFFFFFFF
    th = int(m1457.get(unit, 0) or 0) & 0xFFFFFFFF
    tv = m1458.get(unit, [0, 0])
    lv = m1459.get(unit, [0, 0])
    state = (th, int(tv[0]) & 0xFFFFFFFF, int(tv[1]) & 0xFFFFFFFF,
             int(lv[0]) & 0xFFFFFFFF, int(lv[1]) & 0xFFFFFFFF,
             int(m1460.get(unit, 0) or 0) & 0xFFFFFFFF)
    if slot == 0 and state == summon_empty_state():
        return None
    return {
        'unit': unit,
        'slot': slot,
        'type_hash': th,
        'main_hash': int(tv[0]) & 0xFFFFFFFF,
        'sub_hash': int(tv[1]) & 0xFFFFFFFF,
        'main_level': int(lv[0]),
        'sub_level': int(lv[1]),
        'rank': int(m1460.get(unit, 0) or 0) & 0xFFFFFFFF,
    }


def summon_read_record(save, unit):
    """读取 unit(0-999) 的召唤石记录。返回 dict 或 None(空记录)。"""
    return summon_record_from_maps(summon_maps(save), unit)


def summon_inventory(save):
    """读取完整召唤石背包。返回 (records, equipped, max_slot, unlocked)。
    records 按 SlotID 升序;equipped = 1451 的 4 个 SlotID 列表。"""
    maps = summon_maps(save)
    m1454 = vm(save, ID_SUM_MAXSLOT)
    m1455 = vm(save, ID_SUM_UNLOCKED)
    records = []
    for unit in range(SUMMON_CAPACITY):
        rec = summon_record_from_maps(maps, unit)
        if rec:
            records.append(rec)
    records.sort(key=lambda r: r['slot'])
    eq_recs = save.find(id_type=ID_SUM_EQUIPPED)
    equipped = list(save.get_values(eq_recs[0])) if eq_recs else []
    equipped = [int(v) & 0xFFFFFFFF for v in equipped]
    while len(equipped) < 4:
        equipped.append(0)
    return records, equipped, int(m1454.get(0, 0) or 0) & 0xFFFFFFFF, bool(m1455.get(0, 0))


def summon_register_type(save, type_hash):
    """确保种类已登记进 1452/1453 目录(找不到空行则返回错误消息)。"""
    type_hash = int(type_hash) & 0xFFFFFFFF
    m1452 = vm(save, ID_SUM_CATALOG)
    for u, h in m1452.items():
        if (int(h) & 0xFFFFFFFF) == type_hash:
            set_first(save, ID_SUM_REGISTERED, u, 1, 'uint')
            return None
    for u, h in sorted(m1452.items()):
        if (int(h) & 0xFFFFFFFF) == EMPTY:
            set_first(save, ID_SUM_CATALOG, u, type_hash, 'uint')
            set_first(save, ID_SUM_REGISTERED, u, 1, 'uint')
            return None
    return f'登记目录已满({SUMMON_CATALOG_ROWS} 行),无法登记新种类 0x{type_hash:08X}'


def summon_write_state(save, unit, type_hash, main_hash, sub_hash, main_level, sub_level, rank):
    """写 1457/1458/1459/1460 四个字段。"""
    set_first(save, ID_SUM_TYPE2, unit, int(type_hash) & 0xFFFFFFFF, 'uint')
    trec = save.find_first('uint', ID_SUM_TRAITS, unit)
    if trec is None:
        raise RuntimeError(f'缺少 id_type={ID_SUM_TRAITS} unit={unit} 记录')
    save.set_values(trec, [int(main_hash) & 0xFFFFFFFF, int(sub_hash) & 0xFFFFFFFF])
    lrec = save.find_first('int', ID_SUM_LEVELS, unit)
    if lrec is None:
        raise RuntimeError(f'缺少 id_type={ID_SUM_LEVELS} unit={unit} 记录')
    save.set_values(lrec, [int(main_level), int(sub_level)])
    set_first(save, ID_SUM_RANK, unit, int(rank) & 0xFFFFFFFF, 'uint')


def summon_validate_draft(type_hash, main_hash, sub_hash, main_level, sub_level, rank,
                          natural_warn=True, extra_ok=None):
    """校验召唤石配置。返回 (错误消息 or None, 警告列表)。
    - 种类必须在目录;主加护/副词条必须在目录
    - 等级:主加护 <= min(maxLevel,15);副词条 <= maxLevel
    - 阶级 0-3
    - natural_warn=True 时,若组合不在该种类的 2.0.2 天然词池/等级池则给出警告
    """
    warns = []
    if _sum_key(type_hash) not in SUMCAT_TYPES:
        return f'未知召唤石种类 0x{int(type_hash) & 0xFFFFFFFF:08X}(可用 "summons catalog" 查看)', warns
    if _sum_key(main_hash) not in SUMCAT_MAIN and int(main_hash) & 0xFFFFFFFF != EMPTY:
        return f'未知主加护 0x{int(main_hash) & 0xFFFFFFFF:08X}(可用 "summons traits" 查看)', warns
    if _sum_key(sub_hash) not in SUMCAT_SUB:
        return f'未知副词条 0x{int(sub_hash) & 0xFFFFFFFF:08X}(可用 "summons subparams" 查看)', warns
    ml = int(main_level)
    if ml < 0 or ml > summon_main_max_level(main_hash):
        return f'主加护等级 {ml} 超出上限 {summon_main_max_level(main_hash)}', warns
    sl = int(sub_level)
    if sl < 0 or sl > summon_sub_max_level(sub_hash):
        return f'副词条档位 {sl} 超出上限 {summon_sub_max_level(sub_hash)}', warns
    if int(rank) < 0 or int(rank) > SUMMON_MAX_RANK:
        return f'阶级必须为 0-{SUMMON_MAX_RANK},收到 {rank}', warns
    if natural_warn:
        te = SUMCAT_TYPES.get(_sum_key(type_hash), {})
        pool_m = set(int(x) & 0xFFFFFFFF for x in te.get('mainTraitHashes', []))
        pool_s = set(int(x) & 0xFFFFFFFF for x in te.get('subParamHashes', []))
        lv_m = set(int(x) for x in te.get('mainTraitLevels', []))
        lv_s = set(int(x) for x in te.get('subParamLevels', []))
        if pool_m and (int(main_hash) & 0xFFFFFFFF) not in pool_m:
            warns.append(f'主加护「{summon_trait_name(main_hash)}」不在「{summon_type_name(type_hash)}」的天然词池')
        if pool_s and (int(sub_hash) & 0xFFFFFFFF) not in pool_s:
            warns.append(f'副词条「{summon_sub_name(sub_hash)}」不在「{summon_type_name(type_hash)}」的天然词池')
        if lv_m and ml not in lv_m:
            warns.append(f'主加护等级 {ml} 不在该种类的天然等级集合 {sorted(lv_m)}')
        if lv_s and sl not in lv_s:
            warns.append(f'副词条档位 {sl} 不在该种类的天然档位集合 {sorted(lv_s)}')
    return None, warns


def summon_create(save, type_hash, main_hash, sub_hash, main_level, sub_level, rank,
                  dry=False, natural_warn=True):
    """新增一个召唤石(写入第一个空 unit, SlotID = max+1, 更新 1454, 登记 1452)。
    返回 (错误消息 or None, 新记录 dict or None)。"""
    err, warns = summon_validate_draft(type_hash, main_hash, sub_hash, main_level, sub_level, rank,
                                       natural_warn=natural_warn)
    if err:
        return err, None
    records, equipped, max_slot, unlocked = summon_inventory(save)
    if not unlocked:
        return '存档中召唤系统(1455)未解锁,无法新增召唤石', None
    if max_slot == 0xFFFFFFFF:
        return 'MaxSlotID 已溢出,无法新增', None
    target = None
    for unit in range(SUMMON_CAPACITY):
        if summon_read_record(save, unit) is None:
            target = unit
            break
    if target is None:
        return f'召唤石背包已满({SUMMON_CAPACITY} 槽)', None
    new_slot = max_slot + 1
    if dry:
        return None, {'unit': target, 'slot': new_slot, 'type_hash': int(type_hash) & 0xFFFFFFFF,
                      'main_hash': int(main_hash) & 0xFFFFFFFF, 'sub_hash': int(sub_hash) & 0xFFFFFFFF,
                      'main_level': int(main_level), 'sub_level': int(sub_level), 'rank': int(rank)}
    err = summon_register_type(save, type_hash)
    if err:
        return err, None
    summon_write_state(save, target, type_hash, main_hash, sub_hash, main_level, sub_level, rank)
    set_first(save, ID_SUM_SLOT, target, new_slot, 'uint')
    set_first(save, ID_SUM_MAXSLOT, 0, new_slot, 'uint')
    return None, {'unit': target, 'slot': new_slot, 'type_hash': int(type_hash) & 0xFFFFFFFF,
                  'main_hash': int(main_hash) & 0xFFFFFFFF, 'sub_hash': int(sub_hash) & 0xFFFFFFFF,
                  'main_level': int(main_level), 'sub_level': int(sub_level), 'rank': int(rank)}


def summon_update(save, unit, type_hash, main_hash, sub_hash, main_level, sub_level, rank,
                  natural_warn=True):
    """修改已有召唤石(unit 0-999)。
    种类不变:直接改 1457-1460。
    种类改变:按 PE Patch Tool 语义重建 SlotID(max+1),并把 1451 装备引用迁移到新 SlotID。
    返回 (错误消息 or None, 更新后记录 dict or None)。"""
    cur = summon_read_record(save, unit)
    if cur is None:
        return f'unit {unit} 不是有效的召唤石记录(先 "summons list" 查看)', None
    err, warns = summon_validate_draft(type_hash, main_hash, sub_hash, main_level, sub_level, rank,
                                       natural_warn=natural_warn)
    if err:
        return err, None
    type_hash = int(type_hash) & 0xFFFFFFFF
    if type_hash == cur['type_hash']:
        err = summon_register_type(save, type_hash)
        if err:
            return err, None
        summon_write_state(save, unit, type_hash, main_hash, sub_hash, main_level, sub_level, rank)
        return None, summon_read_record(save, unit)
    # 换种类:分配新 SlotID,迁移 1451 装备引用
    records, equipped, max_slot, unlocked = summon_inventory(save)
    if max_slot == 0xFFFFFFFF:
        return 'MaxSlotID 已溢出,无法更换种类', None
    new_slot = max_slot + 1
    err = summon_register_type(save, type_hash)
    if err:
        return err, None
    summon_write_state(save, unit, type_hash, main_hash, sub_hash, main_level, sub_level, rank)
    set_first(save, ID_SUM_SLOT, unit, new_slot, 'uint')
    set_first(save, ID_SUM_MAXSLOT, 0, new_slot, 'uint')
    # 迁移装备引用:旧 SlotID -> 新 SlotID
    eq_recs = save.find(id_type=ID_SUM_EQUIPPED)
    if eq_recs:
        eq = list(save.get_values(eq_recs[0]))
        changed = False
        for i, v in enumerate(eq):
            if (int(v) & 0xFFFFFFFF) == cur['slot']:
                eq[i] = new_slot
                changed = True
        if changed:
            save.set_values(eq_recs[0], eq)
    return None, summon_read_record(save, unit)


def summon_set_equipped(save, idx, slot_id):
    """设置 1451 装备槽 idx(0-3) 为 SlotID(0=卸下)。"""
    if not (0 <= idx < 4):
        return f'装备槽必须是 1-4,收到 {idx + 1}'
    eq_recs = save.find(id_type=ID_SUM_EQUIPPED)
    if not eq_recs:
        return '存档缺少 1451 装备字段'
    eq = list(save.get_values(eq_recs[0]))
    while len(eq) < 4:
        eq.append(0)
    eq[idx] = int(slot_id) & 0xFFFFFFFF
    save.set_values(eq_recs[0], eq)
    return None


def summon_slot_by_unit(records, unit):
    for r in records:
        if r['unit'] == unit:
            return r['slot']
    return None


def summon_locate(save, slot_or_unit):
    """按槽号(列表第一列,优先)或 unit 定位召唤石记录;找不到返回 None。"""
    n = int(slot_or_unit)
    rec = summon_read_record(save, n)
    if rec is not None:
        return rec
    for r in summon_inventory(save)[0]:
        if r['slot'] == n:
            return r
    return None

# ---- 上限突破 (Overmastery) ----
# 存档:id 1606=效果哈希, 1607=数值;unit = 10000000 + 角色组×1000 + 槽位(0-3)
OM_FIELD_EFFECT, OM_FIELD_VALUE = 1606, 1607
OM_UNIT_BASE, OM_GROUP_STRIDE = 10000000, 1000
OM_VALUE_MAX = 0x03FF  # 1023 = 满值
OM_EFFECTS = {
    '攻击力': 0xC4925BD7,
    '连锁爆发伤害': 0x68B39018,
    '暴击率': 0x45C65767,
    '治疗上限': 0x54929589,
    '体力': 0x52A207B5,
    '普攻伤害上限': 0x43B7581D,
    '奥义伤害上限': 0x4A4C093D,
    '奥义伤害': 0x4E42646B,
    '技能伤害上限': 0x9C555433,
    '技能伤害': 0x9A97C049,
    '昏厥力': 0x6CB38EF3,
    '攻击力(变体)': 0xD75B92C4,
    '连锁爆发伤害(变体)': 0x1890B368,
    '暴击率(变体)': 0x6757C645,
    '治疗上限(变体)': 0x89959254,
    '体力(变体)': 0xB507A252,
    '普攻伤害上限(变体)': 0x1D58B743,
    '奥义伤害上限(变体)': 0x3D094C4A,
    '奥义伤害(变体)': 0x6B64424E,
    '技能伤害上限(变体)': 0x3354559C,
    '技能伤害(变体)': 0x49C0979A,
    '昏厥力(变体)': 0xF38EB36C,
}
OM_EFFECTS_BY_HASH = {v: k for k, v in OM_EFFECTS.items()}

# ---- 上限突破数值换算 ----
# 存档值 1607 是 0~1023 的内部刻度,映射规则(玩家实测 + 游戏 limit_bonus_param.tbl):
#   星级 = floor(log2(存档值)) + 1(临界点在 2 的幂:64→7⭐、128→8⭐、256→9⭐、512→10⭐)
#   显示值 = 该星级的档位值(Lv[star]);512 = 10⭐ = 满档
#   存档值 512~1023 为超出满档的"改档区",线性延伸至 1023→满档×4(实测普攻上限 1023→80%)
_OM_LV_PCT = (1, 1, 2, 4, 6, 8, 10, 12, 16, 20)          # 百分比类 1⭐..10⭐
_OM_LV_ATK = (100, 100, 200, 300, 400, 500, 600, 700, 800, 1000)   # 攻击力(点)
_OM_LV_HP = (100, 200, 400, 500, 600, 800, 1000, 1200, 1600, 2000)  # 体力(点)

# 效果哈希 -> (星级档位表, 单位)
_OM_LV_UNIT = {}
for _n, _h in OM_EFFECTS.items():
    _base = _n.replace('(变体)', '')
    if _base == '攻击力':
        _OM_LV_UNIT[_h] = (_OM_LV_ATK, '点')
    elif _base == '体力':
        _OM_LV_UNIT[_h] = (_OM_LV_HP, '点')
    elif _base == '昏厥力':
        _OM_LV_UNIT[_h] = (_OM_LV_PCT, '点')
    else:
        _OM_LV_UNIT[_h] = (_OM_LV_PCT, '%')
del _n, _h, _base


def om_star(raw_value):
    """存档值 -> 星级(1-10);0/空返回 0。临界点: 2^(星-1)。"""
    raw_value = int(raw_value or 0)
    if raw_value <= 0:
        return 0
    import math
    return min(10, int(math.log2(raw_value)) + 1)


def om_display_value(effect_hash, raw_value):
    """存档值 -> 游戏内显示(按星级档位)。返回如 '16% (9⭐)' / '700点 (9⭐)' / ''(空)。"""
    raw_value = int(raw_value or 0)
    if raw_value <= 0:
        return ''
    h = effect_hash & 0xFFFFFFFF
    lv, unit = _OM_LV_UNIT.get(h, (_OM_LV_PCT, '%'))
    if raw_value <= 512:
        star = om_star(raw_value)
        shown = lv[star - 1]
        return '%d%s (%d⭐)' % (shown, unit, star)
    # 超出满档(512~1023):线性延伸,1023 = 满档×4(实测 20%→80%)
    star10 = lv[9]
    shown = star10 + (raw_value - 512) / (OM_VALUE_MAX - 512) * (star10 * 3)
    return '%.0f%s' % (shown, unit)

def om_unit(group, lane):
    return OM_UNIT_BASE + group * OM_GROUP_STRIDE + lane

def build_roster(save):
    """从存档读取角色名册(id_type 1301): {组号: 角色哈希}。

    名册组号与 PL 编号**不是**同一套顺序(如贝阿朵丽丝 PL2600 在名册组 37)。
    上限突破(id 1606/1607)的组号必须按名册解析,否则会读到别的角色。
    """
    roster = {}
    for r in save.find(id_type=1301):
        v = save.get_first_value(r)
        if v:
            roster[r.unit_id - 10000] = int(v) & 0xFFFFFFFF
    return roster


def chara_group_by_roster(roster, chash):
    """按名册找角色哈希对应的组号;找不到返回 None。"""
    chash = int(chash) & 0xFFFFFFFF
    for g, h in roster.items():
        if h == chash:
            return g
    return None


def chara_hash_of(gid):
    """把 PL 代码/0x 哈希/角色名解析为角色哈希(int);失败返回 None。"""
    gid = (gid or '').strip()
    if not gid:
        return None
    m = gid.upper()
    if m.startswith('0X'):
        try:
            return int(m, 16) & 0xFFFFFFFF
        except ValueError:
            return None
    if m.startswith('PL'):
        for h, g in CHARSCAT.items():
            if g == m:
                return int(h) & 0xFFFFFFFF
    h, pl = find_chara(gid)
    if pl:
        for hh, g in CHARSCAT.items():
            if g == pl:
                return int(hh) & 0xFFFFFFFF
    return None


def char_group(gid, save=None):
    """角色(PLxxxx 或 名称) -> 上限突破组索引(0-40);返回 None 表示无法确定。

    优先用存档名册(id_type 1301)精确映射;无存档时回退 PL 编号/100(近似)。
    """
    chash = chara_hash_of(gid)
    if chash is not None and save is not None:
        g = chara_group_by_roster(build_roster(save), chash)
        if g is not None:
            return g
    # 回退:PL 编号 / 100
    gid = (gid or '').strip()
    m = gid.upper()
    if not (m.startswith('PL') or m.startswith('0X')):
        h, pl = find_chara(gid)
        if pl:
            m = pl
    if not m.startswith('PL'):
        m = 'PL' + m
    if m.startswith('PL') and m[2:].isdigit():
        idx = int(m[2:]) // 100
        if idx < 40:
            return idx
    for h, g in CHARSCAT.items():
        if g == m:
            return int(h) & 0xFFFFFFFF
    return None

def get_overmastery(save, gid):
    """读取某角色 4 槽上限突破,返回 [(效果名, 数值, 原始哈希, 显示值)]。"""
    grp = char_group(gid, save=save)
    if grp is None:
        return None, f'无法识别角色: {gid}'
    m1606 = vm(save, OM_FIELD_EFFECT)
    m1607 = vm(save, OM_FIELD_VALUE)
    rows = []
    for lane in range(4):
        u = om_unit(grp, lane)
        h = m1606.get(u, 0) & 0xFFFFFFFF
        v = m1607.get(u, 0)
        if h in (0, EMPTY):
            rows.append(('空', 0, 0, ''))
        else:
            rows.append((OM_EFFECTS_BY_HASH.get(h, f'0x{h:08X}'), v, h,
                         om_display_value(h, v)))
    return rows, None

def set_overmastery(save, gid, lane, effect_name, value):
    """设置某角色某一槽的上限突破。effect_name 可为中文名/0x哈希/空(清空)。"""
    grp = char_group(gid, save=save)
    if grp is None:
        return f'无法识别角色: {gid}'
    if not (0 <= lane < 4):
        return f'槽位必须是 0-3,收到 {lane}'
    u = om_unit(grp, lane)
    # 清空
    if effect_name in ('', '空', 'clear', 'none'):
        set_first(save, OM_FIELD_EFFECT, u, EMPTY, 'uint')
        set_first(save, OM_FIELD_VALUE, u, 0, 'int')
        return None
    # 解析效果哈希
    q = effect_name.strip()
    if q.lower().startswith('0x'):
        h = int(q, 16) & 0xFFFFFFFF
    else:
        hits = [k for k in OM_EFFECTS if q in k]
        if not hits:
            return f'未知上限突破效果: {effect_name}(可用: {"/".join(OM_EFFECTS)})'
        h = OM_EFFECTS[min(hits, key=len)]
    if value < 0 or value > OM_VALUE_MAX:
        return f'数值超出范围 0-{OM_VALUE_MAX}: {value}'
    set_first(save, OM_FIELD_EFFECT, u, h, 'uint')
    set_first(save, OM_FIELD_VALUE, u, value, 'int')
    return None

def _mix_pool():
    """合成池:所有 V+(名字含"＋")因子的技能(SkillId1∪SkillId2)。
    合成机制(游戏实测+1.3官方):选入两个 V+ 因子 → 全部技能(≤4)洗牌取前2 = 新因子,
    故任意带该主词条 V+ 版本的因子都能通过合成获得合成池中的任意技能作为副词条。"""
    if LEGAL is None:
        return set()
    return {int(x, 16) for x in LEGAL['mix_pool']}

def _drop_pool(sigil_hash):
    """掉落/抽卡副词条池:gem.SkillTypeLotIdForRandom2ndSkill -> skill_type_lot -> skill_lot。"""
    if LEGAL is None:
        return set()
    return {int(x, 16) for x in LEGAL['drop_pool'].get(str(sigil_hash), [])}

def _can_mix(sigil_hash):
    """该因子能否经合成获得副词条(即它能否作为合成结果的模板)。
    实测(用户游戏内):合成 = 选入两个 V+ 因子,四个技能随机混合取前2 = 全新因子,
    结果模板是 Legendary+(名字带"＋")因子。因此只有 V+ 因子本身可作合成结果模板;
    无+版因子(如可怕的漆黑钳蟹因子 0x49434696)在合成界面灰色不可选,不可经合成加副词条。"""
    if LEGAL is None:
        return False
    name = GEMCAT['sigil_info'].get(str(sigil_hash), {}).get('cn') or \
           GEMCAT['sigil_info'].get(str(sigil_hash), {}).get('name') or ''
    return '＋' in name or '+' in name

DUMMY_SKILL_HASH = 0xCAC6AFF2

def _strip_plus_name(name):
    if name.endswith('＋'):
        return name[:-1]
    if name.endswith('+'):
        return name[:-1]
    return name

def sigil_primary_hash(sigil_hash, info=None):
    """返回该因子真正的主词条哈希。

    gem.tbl 中少数 V+ 因子(如 万能药＋/霸体＋/自动药水＋)的 SkillId1 是
    无功能占位技能 0xCAC6AFF2,直接写入存档会导致游戏内因子主词条错误。
    这里先查完整目录中的 primaryTraitId,再退回同名无+版因子的主词条。
    """
    if info is None:
        info = GEMCAT.get('sigil_info', {}).get(str(sigil_hash), {})
    primary = info.get('primary', EMPTY)
    if primary != DUMMY_SKILL_HASH:
        return primary
    # catalog_sigils_full.json 的 primaryTraitId 是 item_id.csv 的权威映射
    for e in SIGILS_FULL.get('sigils', []):
        h = e.get('hash')
        if h and (int(h, 16) & 0xFFFFFFFF) == (sigil_hash & 0xFFFFFFFF):
            pid = e.get('primaryTraitId')
            if pid:
                return gbfr_hash(pid)
    # 兜底:同名无+版因子
    name = info.get('name') or ''
    base_name = _strip_plus_name(name)
    if base_name and base_name != name:
        for hk, e in GEMCAT.get('sigil_info', {}).items():
            if int(hk) & 0xFFFFFFFF != (sigil_hash & 0xFFFFFFFF) and e.get('name') == base_name:
                bp = e.get('primary')
                if bp and bp != DUMMY_SKILL_HASH:
                    return bp
    return primary

def find_item(q):
    q = q.strip().lower()
    if q.startswith('0x'):
        h = int(q, 16) & 0xFFFFFFFF
        return CAT['items'].get(str(h))
    for hk, e in CAT['items'].items():
        if q in e.get('id', '').lower() or q in e.get('en', '').lower() or q in e.get('cn', '').lower():
            return e
    return None

def _norm(q):
    # 把用户输入的半角 + 也归一化为中文目录里的全角 ＋(例如 万能药+ -> 万能药＋)
    return q.replace('V+', 'Ⅴ＋').replace('v+', 'Ⅴ＋').replace('+', '＋').strip().lower()

def find_sigil(q):
    q = q.strip().lower()
    if q.startswith('0x'):
        h = int(q, 16) & 0xFFFFFFFF
        return GEMCAT['sigil_info'].get(str(h))
    qn = _norm(q)
    hits = []
    for hk, e in GEMCAT['sigil_info'].items():
        cn = (e.get('cn') or '').lower()
        en = (e.get('name') or '').lower()
        gid = str(e.get('id', '')).lower()
        if q in cn or q in en or q in gid or (qn and (qn in cn or qn in en)):
            hits.append(e)
    if not hits:
        return None
    def score(e):
        cn = (e.get('cn') or '').lower(); en = (e.get('name') or '').lower()
        if cn == q or en == q or (qn and (cn == qn or en == qn)): return 0
        if cn.startswith(q) or en.startswith(q): return 1
        if '＋' in cn or '+' in en: return 2
        return 3
    return min(hits, key=score)

def sigil_trait_label(h):
    """因子词条哈希 -> 中文显示名(副槽为空时显示“无”)。"""
    h = int(h) & 0xFFFFFFFF
    if h == EMPTY:
        return '无'
    e = GEMCAT['trait_info'].get(str(h), {})
    return e.get('cn') or e.get('name') or f'0x{h:08X}'

def find_trait(q):
    q0 = (q or '').strip()
    if not q0:
        return None
    # 兼容下拉框的 “中文 (English)”、“0xHASH (English)” 等格式
    core, _ = _split_label(q0)
    core_l = (core or q0).lower()
    if core_l.startswith('0x'):
        h = int(core, 16) & 0xFFFFFFFF
        return GEMCAT['trait_info'].get(str(h))
    q = q0.lower()
    qn = _norm(q)
    hits = []
    for hk, e in GEMCAT['trait_info'].items():
        cn = (e.get('cn') or '').lower(); en = (e.get('name') or '').lower()
        if q in cn or q in en or (qn and (qn in cn or qn in en)):
            hits.append(e)
    if not hits:
        if core and core.lower() != q:
            return find_trait(core)
        return None
    def score(e):
        cn = (e.get('cn') or '').lower(); en = (e.get('name') or '').lower()
        if cn == q or en == q or (qn and (cn == qn or en == qn)): return 0
        return 1
    return min(hits, key=score)

def find_chara(q):
    """解析角色标识 -> (角色哈希, PL代码)。

    支持:
      - 角色名(中文/英文,精确或包含,如 '卡塔莉娜' / 'Katalina' / '卡塔莉娜 (PL0200)')
      - PL 代码(PL0000 / 0000)
      - 0x 哈希
    """
    q0 = (q or '').strip()
    if not q0:
        return None, None
    # 1) 形如 'XXX (PL0200)' / 'XXX (Katalina)' 时先提取 PL 代码
    import re
    m = re.search(r'PL\d{4}', q0.upper())
    if m:
        gid = m.group(0)
        for h, g in CHARSCAT.items():
            if g == gid:
                return int(h) & 0xFFFFFFFF, gid
    # 2) 0x 哈希
    q = q0.upper()
    if q.startswith('0X'):
        return int(q, 16) & 0xFFFFFFFF, f'0x{int(q, 16) & 0xFFFFFFFF:08X}'
    # 3) PL 代码 / 纯数字
    if not q.startswith('PL'):
        q = 'PL' + q
    for h, gid in CHARSCAT.items():
        if gid == q:
            return int(h) & 0xFFFFFFFF, gid
    # 4) 角色名匹配(先精确后包含)
    ql = q0.lower()
    for h, gid in CHARSCAT.items():
        e = CHAR_NAMES.get(gid)
        if not e:
            continue
        cn = (e.get('cn') or '').lower(); en = (e.get('en') or '').lower()
        if (cn and cn == ql) or (en and en == ql):
            return int(h) & 0xFFFFFFFF, gid
    for h, gid in CHARSCAT.items():
        e = CHAR_NAMES.get(gid)
        if not e:
            continue
        cn = (e.get('cn') or '').lower(); en = (e.get('en') or '').lower()
        if (cn and (cn in ql or ql in cn)) or (en and (en in ql or ql in en)):
            return int(h) & 0xFFFFFFFF, gid
    return None, None

# ------- save helpers -------
def is_game_running():
    """检测游戏是否正在运行(写入前必须退出游戏,否则存档会被覆盖/锁文件)。"""
    exes = ('granblue_fantasy_relink.exe', 'granblue_fantasy_relink')
    try:
        import subprocess
        out = subprocess.run(
            ['tasklist', '/FO', 'CSV', '/NH'],
            capture_output=True, text=True, timeout=10, creationflags=0x08000000,
        ).stdout.lower()
        return any(ex in out for ex in exes)
    except Exception:
        return False

def open_save(path):
    if not os.path.isfile(path):
        print(f'[错误] 找不到存档: {path}')
        sys.exit(2)
    return GBFRSaveData.open(path)

def vm(save, idt):
    return {r.unit_id: save.get_first_value(r) for r in save.find(id_type=idt)}

def set_first(save, idt, unit, val, kind):
    rec = save.find_first(kind, idt, unit)
    if rec is None:
        raise RuntimeError(f'缺少 id_type={idt} unit={unit} 记录')
    save.set_first_value(rec, val)

def find_empty_sigil_slot(save):
    m2703 = vm(save, ID_2703)
    empty = [s for s, g in m2703.items() if (g & 0xFFFFFFFF) == EMPTY]
    used = [s for s, g in m2703.items() if (g & 0xFFFFFFFF) != EMPTY]
    last = max(used) if used else GEM_SLOT_BASE - 1
    return min([s for s in empty if s > last]) if empty else min(empty)

# ---- 装备上限保护 ----
# 游戏每个角色默认最多装备 12 个因子;第 13 格需要天赋盘"因子栏位解锁"
# (效果哈希 0x7B727910) 点亮,超过上限游戏加载存档会闪退。
SIGIL_SLOT_UNLOCK_EFFECT = 0x7B727910
SIGIL_BASE_SLOTS = 12
SIGIL_MAX_SLOTS = 13


def chara_equipped_count(save, chash):
    """统计某角色当前已装备的因子数(2706=角色哈希且因子非空)。"""
    chash = int(chash) & 0xFFFFFFFF
    m2703 = vm(save, ID_2703)
    m2706 = vm(save, ID_2706)
    n = 0
    for u, g in m2703.items():
        if (g & 0xFFFFFFFF) != EMPTY and (m2706.get(u, 0) & 0xFFFFFFFF) == chash:
            n += 1
    return n


def chara_sigil_cap(save, gid):
    """角色的装备上限:默认 12;点亮了"因子栏位解锁"天赋则为 13。"""
    group = char_group(gid, save=save)
    if group is None:
        return SIGIL_BASE_SLOTS
    # 天赋盘 1606/1607 unit = (10000+组)*10000 + 槽*10 + 孔(槽 0-4, 孔 0-9)
    base = (10000 + group) * 10000
    m1606 = vm(save, 1606)
    m1607 = vm(save, 1607)
    for i in range(5):
        for j in range(10):
            u = base + i * 10 + j
            if (m1606.get(u, 0) & 0xFFFFFFFF) == SIGIL_SLOT_UNLOCK_EFFECT and m1607.get(u, 0) == 1:
                return SIGIL_MAX_SLOTS
    return SIGIL_BASE_SLOTS


def check_equip_limit(save, chash, gid, exclude_slot=None):
    """装备前检查:已装数量 >= 上限则拒绝。exclude_slot 为本次即将改装的槽(不计入)。"""
    chash = int(chash) & 0xFFFFFFFF
    cap = chara_sigil_cap(save, gid)
    # 以角色装备列表(1403)为准统计(游戏按此列表显示装备)
    cur = 0
    rec = _chara_equip_list_rec(save, chash)
    if rec is not None:
        vals = list(save.get_values(rec))
        cur = sum(1 for v in vals if v)
        if exclude_slot is not None:
            m2702 = vm(save, ID_2702)
            ser = m2702.get(exclude_slot, 0) & 0xFFFFFFFF
            if ser and ser in vals:
                cur = max(0, cur - 1)
    else:
        m2706 = vm(save, ID_2706)
        cur = chara_equipped_count(save, chash)
        if exclude_slot is not None and (m2706.get(exclude_slot, 0) & 0xFFFFFFFF) == chash:
            cur = max(0, cur - 1)
    if cur >= cap:
        return ('角色 %s 已装备 %d/%d 个因子,无法再装(第 %d 格需在游戏天赋盘点出"因子栏位解锁")'
                % (chara_label(gid), cur, cap, cap + 1))
    return None

# ---- 装备登记(角色 1403 装备列表) ----
# 游戏判定"因子已装备"依据的是角色 1403 记录中的 2702 序列号列表(13 格),
# 仅写 2706(归属哈希)不够 —— 装备时需把序列号登记进该列表,卸下时移除,
# 否则游戏装备界面不会显示(实测:只写 2706 的因子在游戏内不显示)。
SIGIL_EQUIP_LIST_FIELD = 1403
SIGIL_EQUIP_LIST_MAX = 13


def _chara_equip_list_rec(save, chash):
    """角色 1403 记录(unit = 10000 + 名册组号)。"""
    group = chara_group_by_roster(build_roster(save), int(chash) & 0xFFFFFFFF)
    if group is None:
        return None
    recs = save.find(id_type=SIGIL_EQUIP_LIST_FIELD, unit_id=10000 + group)
    return recs[0] if recs else None


def sigil_equip_register(save, chash, serial):
    """装备:把因子序列号登记进角色 1403 装备列表。返回 True/False(列表已满)。"""
    rec = _chara_equip_list_rec(save, chash)
    if rec is None:
        return False
    serial = int(serial) & 0xFFFFFFFF
    vals = list(save.get_values(rec))
    if serial in vals:
        return True
    for i, v in enumerate(vals):
        if not v:
            vals[i] = serial
            save.set_values(rec, vals)
            return True
    return False


def sigil_equip_unregister(save, chash, serial):
    """卸下:从角色 1403 装备列表移除序列号。"""
    rec = _chara_equip_list_rec(save, chash)
    if rec is None:
        return
    serial = int(serial) & 0xFFFFFFFF
    vals = list(save.get_values(rec))
    if serial in vals:
        vals[vals.index(serial)] = 0
        save.set_values(rec, vals)

# ---- 武器祝福 (Wrightstone) ----
# 存档布局(实测): 2102=物品哈希 2103=序列号 2104=bool 2105=2,槽位 50000~54999
# 词条: 1701/1702 @ 140000000 + (槽-50000)*100 + 词条位(0/1/2),共 3 条词条
# 序列号计数器: 2101[0]
WRIGHT_SLOT_BASE = 50000
WRIGHT_SLOT_COUNT = 5000
WRIGHT_TRAIT_BASE = 140000000
WRIGHT_ITEM_FIELD, WRIGHT_SERIAL_FIELD = 2102, 2103
WRIGHT_FLAG_FIELD, WRIGHT_EXTRA_FIELD = 2104, 2105
WRIGHT_COUNTER_FIELD = 2101
WRIGHT_MAX_LEVEL = 20  # 祝福词条最高等级(游戏实测)

WRIGHT_TYPES = [
    # 名称, 英文, 物品哈希, 默认词条
    ('恐惧祝福', 'Dread Wrightstone', 0x09E6F629, 0xCEB700EE),
    ('活力祝福', 'Vitality Wrightstone', 0x71173866, 0x8D78A19B),
    ('强化祝福', 'Fortification Wrightstone', 0x667EE1D3, 0xF372F096),
    ('封印祝福', 'Sequestration Wrightstone', 0x202A0DB9, 0x6B694D6D),
]
WRIGHT_TYPE_BY_HASH = {t[2]: t for t in WRIGHT_TYPES}

# 祝福专属词条(PE Patch Tool 验证过可出现在祝福上的词条)
WRIGHT_EXTRA_TRAITS = {
    0x9702860F: '灾祸抗性', 0xF687C5EF: '获得经验值', 0xC86F3082: '获得金币',
    0x5E422AE5: '获得MSP', 0x2242921F: '麻痹抗性', 0xCFB48782: '奥义封印抗性',
    0x50B453DD: '能力封印抗性', 0xFB572681: '冰冻抗性', 0xD54F8CA7: '泥沙抗性',
    0x9389CC06: '回复性能', 0x66DE60B1: '防御DOWN抗性', 0x3759A5B9: '昏厥抗性',
    0x973B49AF: '中毒抗性', 0xDD4A701E: '异常抗性', 0x1DC9D7E7: '水牢抗性',
    0x7C84A6B3: '灼热抗性', 0xA2FA9685: '迟缓抗性',
}


def wrightstone_trait_pool(save):
    """祝福可用词条池:存档中祝福上实测出现过的词条 ∪ 祝福专属词条。
    返回 {hash: (中文名, 英文名)}。"""
    pool = {}
    # 1) 存档实测
    m2102 = vm(save, WRIGHT_ITEM_FIELD)
    m1701 = vm(save, 1701)
    for slot in m2102:
        if (m2102[slot] & 0xFFFFFFFF) == EMPTY:
            continue
        base = WRIGHT_TRAIT_BASE + (slot - WRIGHT_SLOT_BASE) * 100
        for lane in range(3):
            h = m1701.get(base + lane, 0) & 0xFFFFFFFF
            if h != EMPTY:
                pool.setdefault(h, (None, None))
    # 2) 祝福专属词条
    for h, cn in WRIGHT_EXTRA_TRAITS.items():
        pool.setdefault(h, (cn, None))
    # 补名称
    out = {}
    for h, (cn, en) in pool.items():
        e = GEMCAT['trait_info'].get(str(h))
        if e:
            out[h] = (e.get('cn') or cn or e.get('name') or '0x%08X' % h,
                      e.get('name') or en or '')
        else:
            out[h] = (cn or '0x%08X' % h, en or '')
    return out


def find_wrightstone_type(q):
    """按名称/英文/哈希解析祝福类型。返回 (名称, 英文, 哈希, 默认词条) 或 None。"""
    q0 = (q or '').strip()
    if not q0:
        return None
    if q0.lower().startswith('0x'):
        h = int(q0, 16) & 0xFFFFFFFF
        return WRIGHT_TYPE_BY_HASH.get(h)
    ql = q0.lower()
    for t in WRIGHT_TYPES:
        if (t[0].lower() in ql) or (t[1].lower() in ql) or (ql in t[0].lower()) or (ql in t[1].lower()):
            return t
    return None


def find_empty_wrightstone_slot(save):
    """找第一个空祝福槽(2102 == EMPTY)。"""
    m2102 = vm(save, WRIGHT_ITEM_FIELD)
    for s in range(WRIGHT_SLOT_BASE, WRIGHT_SLOT_BASE + WRIGHT_SLOT_COUNT):
        if (m2102.get(s, 0) & 0xFFFFFFFF) == EMPTY:
            return s
    return None


def add_wrightstone(save, wtype_hash, traits, dry=False):
    """生成一个武器祝福。traits = [(词条哈希, 等级), ...](最多 3 条)。
    返回槽位;dry=True 只预览。"""
    if not isinstance(wtype_hash, int):
        raise RuntimeError('无效的祝福类型')
    traits = list(traits)[:3]
    for th, lv in traits:
        lv = max(0, min(int(lv), WRIGHT_MAX_LEVEL))
    slot = find_empty_wrightstone_slot(save)
    if slot is None:
        raise RuntimeError('祝福仓库已满(%d 槽)' % WRIGHT_SLOT_COUNT)
    idx = slot - WRIGHT_SLOT_BASE
    m2101 = vm(save, WRIGHT_COUNTER_FIELD)
    serial = int(m2101.get(0, 0)) + 1
    if dry:
        print('[dry] 祝福槽 %d: 物品=0x%08X 序列号=%d 词条=%s' % (
            slot, wtype_hash, serial,
            '; '.join('0x%08X lv%d' % (th, lv) for th, lv in traits)))
        return slot
    set_first(save, WRIGHT_COUNTER_FIELD, 0, serial, 'uint')
    set_first(save, WRIGHT_ITEM_FIELD, slot, wtype_hash, 'uint')
    set_first(save, WRIGHT_SERIAL_FIELD, slot, serial, 'uint')
    set_first(save, WRIGHT_FLAG_FIELD, slot, 0, 'bool')
    set_first(save, WRIGHT_EXTRA_FIELD, slot, 2, 'uint')
    for lane, (th, lv) in enumerate(traits):
        set_first(save, 1701, WRIGHT_TRAIT_BASE + idx * 100 + lane, th, 'uint')
        set_first(save, 1702, WRIGHT_TRAIT_BASE + idx * 100 + lane, max(0, min(int(lv), WRIGHT_MAX_LEVEL)), 'int')
    return slot


def cmd_wrightstone(args):
    """祝福命令: list / traits / add。"""
    save = open_save(args.save)
    if args.action == 'list':
        print('=== 武器祝福类型 ===')
        for name, en, h, dt in WRIGHT_TYPES:
            e = GEMCAT['trait_info'].get(str(dt))
            dname = (e.get('cn') or e.get('name')) if e else '0x%08X' % dt
            print('  %-8s (%s)  0x%08X  默认词条:%s' % (name, en, h, dname))
        return
    if args.action == 'traits':
        pool = wrightstone_trait_pool(save)
        q = (args.query or '').lower()
        for h in sorted(pool):
            cn, en = pool[h]
            if q and q not in cn.lower() and q not in en.lower() and q not in f'0x{h:08X}'.lower():
                continue
            print('  %-14s %-28s 0x%08X' % (cn, en, h))
        print(f'[信息] 祝福词条共 {len(pool)} 种')
        return
    if args.action == 'add':
        wt = find_wrightstone_type(args.wrightstone)
        if wt is None:
            print(f'[错误] 找不到祝福类型: {args.wrightstone}'); return
        name, en, h, _ = wt
        traits = []
        if args.traits:
            for part in args.traits.split(','):
                part = part.strip()
                if not part:
                    continue
                if ':' in part:
                    tname, lv = part.rsplit(':', 1)
                    lv = int(lv) if lv.strip().isdigit() else WRIGHT_MAX_LEVEL
                else:
                    tname, lv = part, WRIGHT_MAX_LEVEL
                pool = wrightstone_trait_pool(save)
                t2 = find_trait(tname)
                th = None
                if t2 is not None:
                    th = next((int(hk) for hk, x in GEMCAT['trait_info'].items() if x is t2), None)
                else:
                    core, _ = _split_label(tname)
                    hex_part = core if core and core.lower().startswith('0x') else tname
                    th = int(hex_part, 16) & 0xFFFFFFFF if hex_part.lower().startswith('0x') else None
                if th is None:
                    print(f'[错误] 找不到词条: {tname}(可用: wrightstone traits 查看)'); return
                traits.append((th, lv))
        if not traits:
            # 默认只写祝福自带的默认词条
            traits = [(wt[3], WRIGHT_MAX_LEVEL)]
        slot = add_wrightstone(save, h, traits, dry=getattr(args, 'dry_run', False))
        if getattr(args, 'dry_run', False):
            return
        bak = save_and_backup(save, args.save, 'wrightstone')
        print(f'[完成] 已生成 {name} (槽{slot}, 序列号={vm(save, WRIGHT_SERIAL_FIELD).get(slot)}) '
              f'备份:{os.path.basename(bak)}')
        return

def legal_secondary_ids(sigil_hash):
    """返回该因子可用的合法副词条 SKILL 哈希集合。

    判定区间 = 固定副词条 ∪ 掉落/抽卡池 ∪ 合成池。
      - 固定副词条:该因子自带 SkillId2(如 + 版固定词条)
      - 掉落/抽卡池:gem.SkillTypeLotIdForRandom2ndSkill 展开(skill_lot 权威)
      - 合成池:所有 V+(名字含"＋")因子的技能 —— 游戏合成 = 选入两个 V+ 因子,
        全部技能(≤4)洗牌取前2 = 新因子。实测(万事屋预览):昏厥Ⅴ＋+天星之炼Ⅴ＋
        可出"昏厥主+天星之炼副";故主词条有 V+ 版本的因子可经合成获得合成池任意技能。
    仅当游戏权威数据(gem_legality.json)缺失时才退回作弊器手工池。
    """
    fixed = GEMCAT['sigil_info'].get(str(sigil_hash), {}).get('secondary', EMPTY)
    allowed = set()
    if fixed != EMPTY:
        allowed.add(fixed)
    if LEGAL is not None:
        # 掉落/抽卡池(游戏权威)
        allowed |= _drop_pool(sigil_hash)
        # 合成池(仅该因子可参与合成时适用)
        if _can_mix(sigil_hash):
            allowed |= _mix_pool()
        return allowed
    # sigils_full (作弊器目录) 提供的 allowedSecondaryTraitIds(兜底)
    for e in SIGILS_FULL.get('sigils', []):
        if e.get('hash') and (int(e['hash'], 16) & 0xFFFFFFFF) == sigil_hash:
            for sid in (e.get('allowedSecondaryTraitIds') or []):
                allowed.add(gbfr_hash(sid))
    return allowed

def add_sigil_to_save(save, gem_hash, level, trait1_hash, trait2_hash, worn=None, dry=False):
    # 安全网:即使调用方传入了 gem.tbl 的占位主词条,也改成真正的主词条
    if trait1_hash == DUMMY_SKILL_HASH:
        trait1_hash = sigil_primary_hash(gem_hash)
    slot = find_empty_sigil_slot(save)
    idx = slot - GEM_SLOT_BASE
    m2701 = vm(save, ID_2701)
    new_count = int(m2701.get(0, 0)) + 1
    if dry:
        print(f'[dry] 槽 {slot}: gem=0x{gem_hash:08X} lv={level} t1=0x{trait1_hash:08X} t2=0x{trait2_hash:08X} worn={("0x%08X" % worn) if worn else "无"} count={new_count}')
        return slot
    set_first(save, ID_2701, 0, new_count, 'uint')
    set_first(save, ID_2702, slot, new_count, 'uint')
    set_first(save, ID_2703, slot, gem_hash, 'uint')
    set_first(save, ID_2704, slot, level, 'int')
    set_first(save, ID_2706, slot, worn if worn else EMPTY, 'uint')
    set_first(save, ID_2707, slot, 0x2, 'uint')
    set_first(save, ID_1701, TRAIT_REC_BASE + idx * 100, trait1_hash, 'uint')
    set_first(save, ID_1702, TRAIT_REC_BASE + idx * 100, level, 'int')
    set_first(save, ID_1701, TRAIT_REC_BASE + idx * 100 + 1, trait2_hash, 'uint')
    set_first(save, ID_1702, TRAIT_REC_BASE + idx * 100 + 1, level, 'int')
    if worn:
        sigil_equip_register(save, worn, new_count)
    return slot

def save_and_backup(save, path, tag, force=False):
    """写入存档并备份。force=False 时检测游戏进程,运行中拒绝写入。
    force=True 时跳过检测强制尝试(游戏运行中大概率文件被占用或退出时被覆盖)。"""
    if not force and is_game_running():
        print('[错误] 检测到游戏正在运行,无法安全写入存档!')
        print('       请先完全退出游戏(含 Steam 云同步)后再修改。')
        raise RuntimeError('game_running')
    stamp = time.strftime('%Y%m%d_%H%M%S')
    bak = f'{path}.{tag}_{stamp}'
    try:
        shutil.copy2(path, bak)
        save.save_over_original(update_hash=True, backup=False, validate=True, fsync=True)
    except OSError as exc:
        print(f'[错误] 写入失败(存档可能被游戏占用): {exc}')
        raise RuntimeError('write_failed')
    if force and is_game_running():
        print('[警告] 强制写入完成,但游戏仍在运行——退出游戏时存档可能被游戏覆盖,修改可能丢失!')
    return bak


def try_save_and_backup(save, path, tag, force=False):
    """GUI 用:保存并备份,失败(游戏运行中/写入失败)返回 (None, 错误消息),不抛异常。"""
    try:
        return save_and_backup(save, path, tag, force=force), None
    except RuntimeError as exc:
        msg = {
            'game_running': '检测到游戏正在运行,无法安全写入存档!\n请先完全退出游戏(含 Steam 云同步)后再修改。',
            'write_failed': '写入失败(存档可能被游戏占用或被其他程序锁定)。',
        }.get(str(exc), str(exc))
        return None, msg

# ------- commands -------
def cmd_items(args):
    save = open_save(args.save)
    m1801 = vm(save, ID_ITEM_ID)
    m1802 = vm(save, ID_ITEM_COUNT)
    rows = []
    for u, h in m1801.items():
        e = CAT['items'].get(h) or CAT['items'].get(str(h))
        name = (e['cn'] or e['en'] or e['id']) if e else f'0x{h:08X}'
        rows.append((u, h, name, m1802.get(u, 0)))
    if args.action == 'list':
        q = (args.query or '').lower()
        for u, h, name, c in rows:
            if q and q not in name.lower() and q not in f'0x{h:08X}'.lower():
                continue
            print(f'  {name:<24} x{c:<6} 0x{h:08X}')
        return
    if args.action == 'set':
        e = find_item(args.query)
        if e is None:
            print(f'[错误] 找不到物品: {args.query}'); return
        h = int(e.get('hash', '0'), 16) if 'hash' in e else next((hh for hh, x in CAT['items'].items() if x is e), None)
        h = int(h)
        slot = next((u for u, v in m1801.items() if (v & 0xFFFFFFFF) == (h & 0xFFFFFFFF)), None)
        if slot is None:
            print(f'[错误] 该物品不在存档中(需先拥有): {e.get("id")}'); return
        rec = save.find_first('int', ID_ITEM_COUNT, slot)
        old = save.get_first_value(rec)
        save.set_first_value(rec, args.count)
        save_and_backup(save, args.save, 'item')
        print(f'[完成] {e.get("cn") or e.get("en") or e.get("id")}: {old} -> {args.count} (槽{slot})')

def cmd_sigils(args):
    save = open_save(args.save)
    if args.action == 'list':
        q = (args.query or '').lower()
        for hk, e in sorted(GEMCAT['sigil_info'].items()):
            h = int(hk) & 0xFFFFFFFF
            name = e.get('cn') or e.get('name')
            if q and q not in name.lower() and q not in e.get('name','').lower() and q not in f'0x{h:08X}'.lower():
                continue
            t2 = e.get('secondary')
            sec = ('+' if t2 and (t2 & 0xFFFFFFFF) != EMPTY else '')
            print(f'  {name:<28} {e.get("name",""):<28} 0x{h:08X} {sec}')
        return
    if args.action == 'add':
        e = find_sigil(args.query)
        if e is None:
            print(f'[错误] 找不到因子: {args.query}'); return
        gem_hash = next((int(hk) for hk, x in GEMCAT['sigil_info'].items() if x is e), None)
        if gem_hash is None:
            print('[错误] 因子目录异常'); return
        info = GEMCAT['sigil_info'][str(gem_hash)]
        primary = sigil_primary_hash(gem_hash, info)
        fixed_sec = info['secondary']
        # level check
        mx = GEMCAT['trait_info'].get(str(primary), {}).get('max_level', 20)
        level = args.level if args.level else mx
        if level > mx:
            print(f'[警告] 等级 {level} 超过主词条上限 {mx},已截断')
            level = mx
        # secondary resolve
        trait2 = fixed_sec
        if args.secondary:
            t2 = find_trait(args.secondary)
            if t2 is None:
                print(f'[错误] 找不到词条: {args.secondary}'); return
            t2h = next((int(hk) for hk, x in GEMCAT['trait_info'].items() if x is t2), None)
            allowed = legal_secondary_ids(gem_hash)
            if _can_mix(gem_hash):
                # V+ 因子可经合成更换副词条:只受合成池/掉落池约束
                if t2h not in allowed:
                    print(f'[错误] 词条「{t2.get("name")}」不是因子「{e.get("cn") or e.get("name")}」的合法副词条')
                    return
            elif fixed_sec in (EMPTY, None):
                if t2h not in allowed:
                    print(f'[错误] 词条「{t2.get("name")}」不是因子「{e.get("cn") or e.get("name")}」的合法副词条')
                    return
            elif t2h != fixed_sec:
                print(f'[错误] 该因子副词条固定为 0x{fixed_sec:08X},不能自定义')
                return
            trait2 = t2h
        # worn
        worn = None
        if args.equip:
            ch, gid = find_chara(args.equip)
            if ch is None:
                print(f'[错误] 找不到角色: {args.equip}'); return
            err = check_equip_limit(save, ch, gid)
            if err:
                print(f'[错误] {err}'); return
            worn = ch
        slot = add_sigil_to_save(save, gem_hash, level, primary, trait2, worn, dry=getattr(args, 'dry_run', False))
        if getattr(args, 'dry_run', False):
            return
        bak = save_and_backup(save, args.save, 'sigil')
        print(f'[完成] 已生成 {e.get("cn") or e.get("name")} (槽{slot}, 等级{level}) 备份:{os.path.basename(bak)}')

def cmd_chars(args):
    save = open_save(args.save)
    m2702 = vm(save, ID_2702)
    m2703 = vm(save, ID_2703); m2704 = vm(save, ID_2704); m2706 = vm(save, ID_2706)
    m2707 = vm(save, ID_2707)
    m1701 = vm(save, ID_1701); m1702 = vm(save, ID_1702)
    if args.action == 'list':
        equips = {}
        for u, g in m2703.items():
            if (g & 0xFFFFFFFF) == EMPTY: continue
            worn = m2706.get(u)
            if worn and worn != EMPTY:
                equips.setdefault(worn, []).append(u)
        for h, gid in CHARSCAT.items():
            n = len(equips.get(int(h) & 0xFFFFFFFF, []))
            if n:
                print(f'  {chara_label(gid)} [{gid}] (0x{int(h)&0xFFFFFFFF:08X}): {n} 个因子')
        return
    ch, gid = find_chara(args.chara)
    if ch is None:
        print(f'[错误] 找不到角色: {args.chara}'); return
    if args.action == 'sigils':
        mine = [u for u, g in m2703.items() if (g & 0xFFFFFFFF) != EMPTY and m2706.get(u) == ch]
        print(f'=== {chara_label(gid)} 装备的因子 ===')
        for u in sorted(mine):
            idx = u - GEM_SLOT_BASE
            g = m2703.get(u)
            e = GEMCAT['sigil_info'].get(str(g))
            t1 = m1701.get(TRAIT_REC_BASE + idx * 100)
            t2 = m1701.get(TRAIT_REC_BASE + idx * 100 + 1)
            name = (e.get('cn') or e.get('name')) if e else f'0x{g:08X}'
            line = f'  槽{u}: {name:<24} lv{m2704.get(u)}'
            if t1:
                line += f'  主:{sigil_trait_label(t1)}'
            if t2:
                line += f'  副:{sigil_trait_label(t2)}'
            print(line)
        return
    if args.action == 'clear':
        changed = 0
        for u in [u for u, g in m2703.items() if (g & 0xFFFFFFFF) != EMPTY and m2706.get(u) == ch]:
            set_first(save, ID_2706, u, EMPTY, 'uint')
            sigil_equip_unregister(save, ch, m2702.get(u, 0))
            changed += 1
        save_and_backup(save, args.save, 'unequip')
        print(f'[完成] 已卸下 {chara_label(gid)} 的 {changed} 个因子')
        return
    if args.action == 'unequip':
        slot = int(args.sigil)
        if slot not in m2703 or (m2703.get(slot, EMPTY) & 0xFFFFFFFF) == EMPTY:
            print(f'[错误] 槽 {slot} 为空'); return
        set_first(save, ID_2706, slot, EMPTY, 'uint')
        sigil_equip_unregister(save, ch, m2702.get(slot, 0))
        save_and_backup(save, args.save, 'unequip')
        print(f'[完成] 槽{slot} 已从 {chara_label(gid)} 卸下')
        return
    if args.action == 'equip':
        # args.sigil is a slot number OR sigil name
        slot = None
        try:
            slot = int(args.sigil)
        except ValueError:
            e = find_sigil(args.sigil)
            if e is None:
                print(f'[错误] 找不到因子: {args.sigil}'); return
            gh = int(e['hash'], 16) if 'hash' in e else None
            slot = next((u for u, g in m2703.items() if (g & 0xFFFFFFFF) == gh), None)
            if slot is None:
                print('[错误] 存档里没有该因子,先用 sigils add 生成'); return
        if slot not in m2703 or (m2703.get(slot, EMPTY) & 0xFFFFFFFF) == EMPTY:
            print(f'[错误] 槽 {slot} 为空'); return
        # 装备上限检查(该槽已属于目标角色时不计入新增)
        excl = slot if (m2706.get(slot, 0) & 0xFFFFFFFF) == (ch & 0xFFFFFFFF) else None
        err = check_equip_limit(save, ch, gid, exclude_slot=excl)
        if err:
            print(f'[错误] {err}'); return
        # 装备:写 2706 + 规范化 2707(装备行低 2 位 = 2)+ 登记 1403 装备列表
        set_first(save, ID_2706, slot, ch, 'uint')
        set_first(save, ID_2707, slot, (m2707.get(slot, 0) & ~3) | 2, 'uint')
        sigil_equip_register(save, ch, m2702.get(slot, 0))
        save_and_backup(save, args.save, 'equip')
        print(f'[完成] 槽{slot} 已装备到 {chara_label(gid)}')

def cmd_summons(args):
    """召唤石(DLC 2.0 背包)命令: list / show / set / add / equip / unequip /
    catalog / traits / subparams / legacy。所有显示均为真实名称(哈希已反差)。"""
    save = open_save(args.save)
    if args.action == 'catalog':
        q = (args.query or '').lower()
        print('=== 召唤石种类目录(%d 种) ===' % len(SUMCAT_TYPES))
        for hk, e in sorted(SUMCAT_TYPES.items()):
            cn = e.get('cn') or ''
            en = e.get('en') or ''
            if q and q not in cn.lower() and q not in en.lower() and q not in f'0x{int(hk)&0xFFFFFFFF:08X}'.lower():
                continue
            tier = e.get('tier') or ''
            mode = e.get('mode') or ''
            print('  %-30s %-20s 档位%s %s 0x%08X' % (
                cn, ('(%s)' % en) if en else '', tier, ('[%s]' % mode) if mode else '', int(hk) & 0xFFFFFFFF))
        print(f'[信息] 种类目录共 {len(SUMCAT_TYPES)} 种')
        return
    if args.action == 'traits':
        q = (args.query or '').lower()
        print('=== 主加护目录(%d 种) ===' % len(SUMCAT_MAIN))
        for hk, e in sorted(SUMCAT_MAIN.items()):
            cn = e.get('cn') or ''
            en = e.get('en') or ''
            if q and q not in cn.lower() and q not in en.lower() and q not in f'0x{int(hk)&0xFFFFFFFF:08X}'.lower():
                continue
            print('  %-16s %-26s 等级上限%d 0x%08X' % (cn, ('(%s)' % en) if en else '',
                                                      e.get('maxLevel', 15), int(hk) & 0xFFFFFFFF))
        print(f'[信息] 主加护目录共 {len(SUMCAT_MAIN)} 种')
        return
    if args.action == 'subparams':
        q = (args.query or '').lower()
        print('=== 副词条目录(%d 种) ===' % len(SUMCAT_SUB))
        for hk, e in sorted(SUMCAT_SUB.items()):
            cn = e.get('cn') or ''
            if q and q not in cn.lower() and q not in f'0x{int(hk)&0xFFFFFFFF:08X}'.lower():
                continue
            print('  %-30s 档位上限%d %s 0x%08X' % (cn, e.get('maxLevel', 9),
                                                    ('百分比' if e.get('isPercent') else '数值'), int(hk) & 0xFFFFFFFF))
        print(f'[信息] 副词条目录共 {len(SUMCAT_SUB)} 种')
        return
    if args.action == 'legacy':
        print('=== 旧版 3101-3115 记录(含义未完全确认,只读展示) ===')
        m3101 = vm(save, 3101); m3102 = vm(save, 3102); m3113 = vm(save, 3113)
        m3114 = vm(save, 3114); m3115 = vm(save, 3115)
        units = sorted(set(m3101) | set(m3102) | set(m3113) | set(m3114) | set(m3115))
        for u in units:
            worn = m3101.get(u)
            ch = chara_label_by_hash(worn) if worn and (worn & 0xFFFFFFFF) != EMPTY else '未装备'
            t = m3113.get(u)
            print(f'  槽{u}: 角色={ch} 等级={m3102.get(u,0)} 3113[0]=0x{int(t or 0)&0xFFFFFFFF:08X} '
                  f'3114=0x{int(m3114.get(u,0))&0xFFFFFFFF:08X} 3115={m3115.get(u,0)}')
        return

    records, equipped, max_slot, unlocked = summon_inventory(save)
    if args.action == 'list':
        q = (args.query or '').lower()
        show_all = getattr(args, 'all', False)
        print('=== 召唤石背包(%d/%d%s) ===' % (
            len(records), SUMMON_CAPACITY, ' · 已解锁' if unlocked else ' · 未解锁'))
        if show_all:
            print('   (--all: 显示全部 1000 行,含空位)')
        eq_set = set(int(v) & 0xFFFFFFFF for v in equipped if v)
        for r in records:
            if q and q not in summon_type_name(r['type_hash']).lower() and \
                    q not in summon_trait_name(r['main_hash']).lower() and \
                    q not in summon_sub_name(r['sub_hash']).lower() and \
                    q not in f'0x{r["type_hash"]:08X}'.lower():
                continue
            mark = '★' if r['slot'] in eq_set else ' '
            print('  %s槽%-4d %-32s 主:%s Lv%-2d 副:%s 档%-2d 阶级%d 0x%08X' % (
                mark, r['slot'], summon_type_name(r['type_hash']),
                summon_trait_name(r['main_hash']), r['main_level'],
                summon_sub_name(r['sub_hash']), r['sub_level'], r['rank'], r['type_hash']))
        if show_all:
            maps = summon_maps(save)
            empty_rows = [u for u in range(SUMMON_CAPACITY) if summon_record_from_maps(maps, u) is None]
            print(f'   (空 unit {len(empty_rows)} 个: {",".join(str(u) for u in empty_rows[:20])}...)')
        return
    if args.action == 'show':
        r = summon_locate(save, args.unit)
        if r is None:
            print(f'[错误] 找不到槽/unit {args.unit}(先 "summons list" 查看)'); return
        eq_set = set(int(v) & 0xFFFFFFFF for v in equipped if v)
        print(f'unit {r["unit"]} (槽 {r["slot"]})')
        print(f'  种类  : {summon_type_name(r["type_hash"], with_en=True)} 0x{r["type_hash"]:08X}')
        print(f'  主加护: {summon_trait_name(r["main_hash"], with_en=True)} Lv{r["main_level"]} 0x{r["main_hash"]:08X}')
        print(f'  副词条: {summon_sub_name(r["sub_hash"])} 档{r["sub_level"]} 0x{r["sub_hash"]:08X}')
        print(f'  阶级  : {r["rank"]}  装备: {"是(装备槽 " + ",".join(str(i+1) for i, v in enumerate(equipped) if (int(v) & 0xFFFFFFFF) == r["slot"]) + ")" if r["slot"] in eq_set else "否"}')
        return

    def _resolve_main_sub(args2, cur):
        """解析 --main/--sub(可空 = 沿用现有值)。返回 (main_hash, sub_hash) 或错误。"""
        main_h, sub_h = cur['main_hash'], cur['sub_hash']
        if getattr(args2, 'main', None):
            mh = summon_find_main(args2.main)
            if mh is None:
                print(f'[错误] 找不到主加护: {args2.main}(可用 "summons traits" 查看)'); return None, None
            main_h = mh
        if getattr(args2, 'sub', None):
            sh = summon_find_sub(args2.sub)
            if sh is None:
                print(f'[错误] 找不到副词条: {args2.sub}(可用 "summons subparams" 查看)'); return None, None
            sub_h = sh
        return main_h, sub_h

    def _levels(args2, cur):
        ml = cur['main_level'] if getattr(args2, 'main_level', None) is None else int(args2.main_level)
        sl = cur['sub_level'] if getattr(args2, 'sub_level', None) is None else int(args2.sub_level)
        return ml, sl

    if args.action == 'set':
        cur = summon_locate(save, args.unit)
        if cur is None:
            print(f'[错误] 找不到槽/unit {args.unit}(先 "summons list" 查看)'); return
        type_h = cur['type_hash']
        if getattr(args, 'type', None):
            th = summon_find_type(args.type)
            if th is None:
                print(f'[错误] 找不到召唤石种类: {args.type}(可用 "summons catalog" 查看)'); return
            type_h = th
        main_h, sub_h = _resolve_main_sub(args, cur)
        if main_h is None:
            return
        ml, sl = _levels(args, cur)
        rank = cur['rank'] if getattr(args, 'rank', None) is None else int(args.rank)
        err, warns = summon_validate_draft(type_h, main_h, sub_h, ml, sl, rank, natural_warn=True)
        if err:
            print(f'[错误] {err}'); return
        for w in warns:
            print(f'[警告] {w}')
        unit = cur['unit']
        err2, updated = summon_update(save, unit, type_h, main_h, sub_h, ml, sl, rank)
        if err2:
            print(f'[错误] {err2}'); return
        bak = save_and_backup(save, args.save, 'summon')
        print(f'[完成] unit {unit} 已更新(槽 {updated["slot"]}) 备份:{os.path.basename(bak)}')
        print(f'  {summon_type_name(updated["type_hash"])} 主:{summon_trait_name(updated["main_hash"])} Lv{updated["main_level"]} '
              f'副:{summon_sub_name(updated["sub_hash"])} 档{updated["sub_level"]} 阶级{updated["rank"]}')
        return
    if args.action == 'add':
        th = summon_find_type(args.type)
        if th is None:
            print(f'[错误] 找不到召唤石种类: {args.type}(可用 "summons catalog" 查看)'); return
        te = SUMCAT_TYPES.get(_sum_key(th), {})
        # 默认主加护/副词条:该种类 2.0.2 天然词池第一项
        dummy = {'main_hash': EMPTY, 'sub_hash': 0, 'main_level': 0, 'sub_level': 0}
        main_h, sub_h = _resolve_main_sub(args, dummy)
        if main_h is None:
            return
        if main_h == EMPTY:
            pool_m = [int(x) & 0xFFFFFFFF for x in te.get('mainTraitHashes', [])]
            main_h = pool_m[0] if pool_m else None
            if main_h is None:
                print('[错误] 需要指定 --main 主加护(目录中无默认)'); return
        if sub_h == 0 or sub_h == EMPTY:
            pool_s = [int(x) & 0xFFFFFFFF for x in te.get('subParamHashes', [])]
            sub_h = pool_s[0] if pool_s else None
            if sub_h is None:
                print('[错误] 需要指定 --sub 副词条(目录中无默认)'); return
        ml = args.main_level if getattr(args, 'main_level', None) is not None else summon_main_max_level(main_h)
        sl = args.sub_level if getattr(args, 'sub_level', None) is not None else summon_sub_max_level(sub_h)
        rank = args.rank if getattr(args, 'rank', None) is not None else 3
        err, warns = summon_validate_draft(th, main_h, sub_h, ml, sl, rank, natural_warn=True)
        if err:
            print(f'[错误] {err}'); return
        for w in warns:
            print(f'[警告] {w}')
        dry = getattr(args, 'dry_run', False)
        err2, rec = summon_create(save, th, main_h, sub_h, ml, sl, rank, dry=dry)
        if err2:
            print(f'[错误] {err2}'); return
        if dry:
            print(f'[dry] 将新增: {summon_type_name(rec["type_hash"])} 主:{summon_trait_name(rec["main_hash"])} Lv{rec["main_level"]} '
                  f'副:{summon_sub_name(rec["sub_hash"])} 档{rec["sub_level"]} 阶级{rec["rank"]} (槽{rec["slot"]}, unit {rec["unit"]})')
            return
        # 装备(可选 --equip 1-4)
        if getattr(args, 'equip', None):
            idx = int(args.equip) - 1
            e = summon_set_equipped(save, idx, rec['slot'])
            if e:
                print(f'[错误] {e}'); return
        bak = save_and_backup(save, args.save, 'summon')
        print(f'[完成] 已新增: {summon_type_name(rec["type_hash"])} (槽{rec["slot"]}, unit {rec["unit"]}) 备份:{os.path.basename(bak)}')
        print(f'  主:{summon_trait_name(rec["main_hash"])} Lv{rec["main_level"]} 副:{summon_sub_name(rec["sub_hash"])} '
              f'档{rec["sub_level"]} 阶级{rec["rank"]}' + (f' 已装备到槽{args.equip}' if getattr(args, 'equip', None) else ''))
        return
    if args.action == 'equip':
        idx = int(args.slot) - 1
        r = summon_locate(save, args.unit)
        if r is None:
            print(f'[错误] 找不到槽/unit {args.unit}(先 "summons list" 查看)'); return
        err = summon_set_equipped(save, idx, r['slot'])
        if err:
            print(f'[错误] {err}'); return
        bak = save_and_backup(save, args.save, 'summon_equip')
        print(f'[完成] 装备槽{args.slot} <- {summon_type_name(r["type_hash"])} (槽{r["slot"]}) 备份:{os.path.basename(bak)}')
        return
    if args.action == 'unequip':
        idx = int(args.slot) - 1
        err = summon_set_equipped(save, idx, 0)
        if err:
            print(f'[错误] {err}'); return
        bak = save_and_backup(save, args.save, 'summon_unequip')
        print(f'[完成] 装备槽{args.slot} 已卸下 备份:{os.path.basename(bak)}')
        return

def cmd_loadout(args):
    save = open_save(args.save)
    m2702 = vm(save, ID_2702)
    m2703 = vm(save, ID_2703); m2704 = vm(save, ID_2704); m2706 = vm(save, ID_2706)
    m2707 = vm(save, ID_2707)
    ld_dir = WRITE_DIR
    os.makedirs(ld_dir, exist_ok=True)
    if args.action == 'list':
        for fn in sorted(os.listdir(ld_dir)):
            if fn.endswith('.json'):
                print('  ', fn[:-5])
        return
    if args.action == 'save':
        ch, gid = find_chara(args.chara)
        mine = [u for u, g in m2703.items() if (g & 0xFFFFFFFF) != EMPTY and m2706.get(u) == ch]
        data = {'chara': gid, 'sigils': [{'slot': u, 'gem': m2703[u], 'level': m2704.get(u)} for u in sorted(mine)]}
        with open(os.path.join(ld_dir, args.name + '.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        print(f'[完成] 已保存 {chara_label(gid)} 的 {len(data["sigils"])} 个因子配装 -> loadouts/{args.name}.json')
        return
    if args.action == 'restore':
        p = os.path.join(ld_dir, args.name + '.json')
        if not os.path.exists(p):
            print(f'[错误] 找不到配装: {args.name}'); return
        data = json.load(open(p, encoding='utf-8'))
        ch, gid = find_chara(data.get('chara', args.name))
        # unequip all from that char
        for u in [u for u, g in m2703.items() if (g & 0xFFFFFFFF) != EMPTY and m2706.get(u) == ch]:
            set_first(save, ID_2706, u, EMPTY, 'uint')
        # equip saved ones (they must still exist in the save by gem+slot)
        ok = 0
        for s in data.get('sigils', []):
            u = s['slot']
            if u in m2703 and (m2703[u] & 0xFFFFFFFF) == s['gem']:
                set_first(save, ID_2706, u, ch, 'uint')
                set_first(save, ID_2707, u, (m2707.get(u, 0) & ~3) | 2, 'uint')
                sigil_equip_register(save, ch, m2702.get(u, 0))
                ok += 1
        save_and_backup(save, args.save, 'loadout')
        print(f'[完成] 已恢复配装 {args.name} 到 {chara_label(gid)} (装备 {ok}/{len(data.get("sigils",[]))})')

def cmd_overmastery(args):
    save = open_save(args.save)
    # 显示用角色名(输入可能是名字或 PL 代码)
    _, _gid = find_chara(args.chara)
    disp = chara_label(_gid) if _gid else args.chara
    if args.action == 'list':
        rows, err = get_overmastery(save, args.chara)
        if err:
            print(f'[错误] {err}'); return
        print(f'=== {disp} 上限突破 (Overmastery) ===')
        print('     (存档值 512=满档/10⭐, 1023=80% 改档上限)')
        for i, (name, val, h, dispv) in enumerate(rows):
            if name == '空':
                print(f'  槽{i}: (空)')
            else:
                print(f'  槽{i}: {name:<12} 显示={dispv:<11} 存档值={val}/1023  0x{h:08X}')
        return
    if args.action == 'set':
        err = set_overmastery(save, args.chara, args.lane, args.effect, args.value)
        if err:
            print(f'[错误] {err}'); return
        save_and_backup(save, args.save, 'overmastery')
        print(f'[完成] {disp} 槽{args.lane} 已设置: {args.effect} = {args.value}')
        rows, _ = get_overmastery(save, args.chara)
        for i, (name, val, h, dispv) in enumerate(rows):
            if name == '空':
                print(f'  槽{i}: (空)')
            else:
                print(f'  槽{i}: {name:<12} 显示={dispv:<11} 存档值={val}/1023  0x{h:08X}')
    if args.action == 'clear':
        err = set_overmastery(save, args.chara, args.lane, '', 0)
        if err:
            print(f'[错误] {err}'); return
        save_and_backup(save, args.save, 'overmastery')
        print(f'[完成] {disp} 槽{args.lane} 已清空')

def cmd_crab(args):
    """小钳蟹收集功能:改小钳蟹/漆黑小钳蟹数量 + 漆黑蟹像 + 完成蟹收集任务。"""
    save = open_save(args.save)
    # 两种小钳蟹
    targets = []
    if args.wee is not None:
        targets.append(('小钳蟹', 0xEE2559C6, args.wee))
    if args.dark is not None:
        targets.append(('漆黑小钳蟹', 0x9FBA96D1, args.dark))
    if not targets:
        targets.append(('小钳蟹', 0xEE2559C6, args.wee if args.wee is not None else args.count))
        targets.append(('漆黑小钳蟹', 0x9FBA96D1, args.count))
    m1801 = vm(save, ID_ITEM_ID)
    for label, h, cnt in targets:
        slot = next((u for u, v in m1801.items() if (v & 0xFFFFFFFF) == (h & 0xFFFFFFFF)), None)
        if slot is None:
            print(f'[警告] 存档中未找到「{label}」(需先拥有该物品)')
            continue
        rec = save.find_first('int', ID_ITEM_COUNT, slot)
        old = save.get_first_value(rec)
        save.set_first_value(rec, cnt)
        print(f'[物品] {label}: {old} -> {cnt} (槽{slot})')
    # 漆黑蟹像(可选)
    if args.statue:
        h = 0x076A9F41
        slot = next((u for u, v in m1801.items() if (v & 0xFFFFFFFF) == h), None)
        if slot is not None:
            rec = save.find_first('int', ID_ITEM_COUNT, slot)
            old = save.get_first_value(rec)
            save.set_first_value(rec, 1)
            print(f'[奖励] 漆黑蟹像: {old} -> 1 (槽{slot})')
        else:
            print('[警告] 存档中未找到「漆黑蟹像」')
    # 完成 DLC 蟹收集任务
    hit, changed = complete_crab_quests(save)
    print(f'[任务] 命中的蟹任务 {hit} 个,改动 {changed} 个标志')
    save_and_backup(save, args.save, 'crab')
    print('[完成] 小钳蟹功能已写入(自动备份 + 重算校验和)')

def complete_crab_quests(save):
    """把本体 200001 与 DLC 链 290002~290015 的蟹收集任务置为完成。"""
    key_rec = save.find_first('uint', 2550, 0)
    if key_rec is None:
        rows = save.find(id_type=2550)
        key_rec = rows[0] if rows else None
    if key_rec is None:
        return 0, 0
    keys = list(save.get_values(key_rec))
    status_rec = save.find_first('uint', 2551, 0) or (save.find(id_type=2551) or [None])[0]
    viewed_rec = save.find_first('bool', 2554, 0) or (save.find(id_type=2554) or [None])[0]
    done_rec = save.find_first('bool', 2555, 0) or (save.find(id_type=2555) or [None])[0]
    status = list(save.get_values(status_rec)) if status_rec else []
    viewed = list(save.get_values(viewed_rec)) if viewed_rec else []
    done = list(save.get_values(done_rec)) if done_rec else []
    crab = set(range(0x290002, 0x290015 + 1)) | {0x200001}
    changed = 0; hit = 0
    for idx, qid in enumerate(keys):
        if (qid & 0xFFFFFFFF) not in crab:
            continue
        hit += 1
        if status_rec is not None and idx < len(status) and int(status[idx]) < 1:
            status[idx] = 1; changed += 1
        if viewed_rec is not None and idx < len(viewed) and not viewed[idx]:
            viewed[idx] = True; changed += 1
        if done_rec is not None and idx < len(done) and not done[idx]:
            done[idx] = True; changed += 1
    if changed:
        if status_rec is not None: save.set_values(status_rec, status)
        if viewed_rec is not None: save.set_values(viewed_rec, viewed)
        if done_rec is not None: save.set_values(done_rec, done)
    return hit, changed

def main():
    ap = argparse.ArgumentParser(description='GBFR 简易作弊器')
    ap.add_argument('--save', default=DEFAULT_SAVE, help='存档路径')
    sub = ap.add_subparsers(dest='cmd')

    p = sub.add_parser('items'); pa = p.add_subparsers(dest='action')
    p1 = pa.add_parser('list'); p1.add_argument('query', nargs='?')
    p2 = pa.add_parser('set'); p2.add_argument('query'); p2.add_argument('count', type=int)

    p = sub.add_parser('sigils'); pa = p.add_subparsers(dest='action')
    p1 = pa.add_parser('list'); p1.add_argument('query', nargs='?')
    p2 = pa.add_parser('add'); p2.add_argument('query'); p2.add_argument('--level', type=int)
    p2.add_argument('--secondary'); p2.add_argument('--equip'); p2.add_argument('--dry-run', action='store_true')

    p = sub.add_parser('chars'); pa = p.add_subparsers(dest='action')
    p1 = pa.add_parser('list')
    for act in ('sigils', 'equip', 'unequip', 'clear'):
        pp = pa.add_parser(act); pp.add_argument('chara')
        if act in ('equip', 'unequip'):
            pp.add_argument('sigil')

    p = sub.add_parser('summons', help='召唤石(DLC 2.0 背包): 列表/修改/新增/装备,真实名称显示')
    pa = p.add_subparsers(dest='action')
    p1 = pa.add_parser('list', help='列出背包中的召唤石(真实名称)')
    p1.add_argument('query', nargs='?', help='关键词过滤(名称/0x)')
    p1.add_argument('--all', action='store_true', help='显示全部 1000 行(含空位)')
    p2 = pa.add_parser('show', help='查看单个召唤石详情')
    p2.add_argument('unit', type=int)
    p3 = pa.add_parser('set', help='修改已有召唤石: set <unit> [--type 种类] [--main 主加护] [--sub 副词条] [--main-level N] [--sub-level N] [--rank N]')
    p3.add_argument('unit', type=int)
    p3.add_argument('--type', help='新种类(留空 = 不变;换种类会重建 SlotID 并迁移装备引用)')
    p3.add_argument('--main', help='主加护(留空 = 不变)')
    p3.add_argument('--sub', help='副词条(留空 = 不变)')
    p3.add_argument('--main-level', type=int)
    p3.add_argument('--sub-level', type=int)
    p3.add_argument('--rank', type=int)
    p4 = pa.add_parser('add', help='新增召唤石: add <种类> [--main 主加护] [--sub 副词条] [--main-level N] [--sub-level N] [--rank N] [--equip 1-4] [--dry-run]')
    p4.add_argument('type')
    p4.add_argument('--main')
    p4.add_argument('--sub')
    p4.add_argument('--main-level', type=int)
    p4.add_argument('--sub-level', type=int)
    p4.add_argument('--rank', type=int)
    p4.add_argument('--equip', type=int, help='新增后直接装备到槽 1-4')
    p4.add_argument('--dry-run', action='store_true')
    p5 = pa.add_parser('equip', help='装备: equip <1-4> <unit>')
    p5.add_argument('slot', type=int)
    p5.add_argument('unit', type=int)
    p6 = pa.add_parser('unequip', help='卸下装备槽: unequip <1-4>')
    p6.add_argument('slot', type=int)
    p7 = pa.add_parser('catalog', help='列出召唤石种类目录(189 种,真实名称)')
    p7.add_argument('query', nargs='?')
    p8 = pa.add_parser('traits', help='列出主加护目录')
    p8.add_argument('query', nargs='?')
    p9 = pa.add_parser('subparams', help='列出副词条目录')
    p9.add_argument('query', nargs='?')
    p10 = pa.add_parser('legacy', help='旧版 3101-3115 记录(只读)')

    p = sub.add_parser('loadout'); pa = p.add_subparsers(dest='action')
    p1 = pa.add_parser('list')
    p2 = pa.add_parser('save'); p2.add_argument('name'); p2.add_argument('chara')
    p3 = pa.add_parser('restore'); p3.add_argument('name')

    p = sub.add_parser('overmastery', help='上限突破(Overmastery): 查看/设置角色 4 条突破属性')
    pa = p.add_subparsers(dest='action')
    p1 = pa.add_parser('list'); p1.add_argument('chara')
    p2 = pa.add_parser('set'); p2.add_argument('chara'); p2.add_argument('lane', type=int)
    p2.add_argument('effect', help='效果名(攻击力/体力/暴击率/技能伤害上限…或 0x哈希,空=清空)')
    p2.add_argument('value', type=int, help='数值 0-1023(1023=满值)')
    p3 = pa.add_parser('clear'); p3.add_argument('chara'); p3.add_argument('lane', type=int)

    p = sub.add_parser('crab', help='小钳蟹收集: 改小钳蟹/漆黑小钳蟹数量 + 漆黑蟹像 + 完成收集任务')
    p.add_argument('--wee', type=int, help='普通小钳蟹数量')
    p.add_argument('--dark', type=int, help='漆黑小钳蟹数量')
    p.add_argument('--count', type=int, default=20, help='默认数量(未指定 --wee/--dark 时两种都设为该值)')
    p.add_argument('--statue', action='store_true', help='把漆黑蟹像设为 1 并完成收集任务')

    p = sub.add_parser('wrightstone', help='武器祝福: 查看类型/词条, 生成祝福')
    pa = p.add_subparsers(dest='action')
    p1 = pa.add_parser('list', help='列出 4 种祝福类型')
    p1 = pa.add_parser('traits', help='列出祝福可用词条')
    p1.add_argument('query', nargs='?')
    p2 = pa.add_parser('add', help='生成祝福: add <祝福名> --traits "暴击率:20,挑衅:15,攻击力:10"')
    p2.add_argument('wrightstone')
    p2.add_argument('--traits', help='词条与等级,逗号分隔,格式 "词条:等级"(等级 0-20,默认 20)')
    p2.add_argument('--dry-run', action='store_true', help='只预览不写入')

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help(); return
    try:
        if args.cmd == 'items': cmd_items(args)
        elif args.cmd == 'sigils': cmd_sigils(args)
        elif args.cmd == 'chars': cmd_chars(args)
        elif args.cmd == 'summons': cmd_summons(args)
        elif args.cmd == 'loadout': cmd_loadout(args)
        elif args.cmd == 'overmastery': cmd_overmastery(args)
        elif args.cmd == 'crab': cmd_crab(args)
        elif args.cmd == 'wrightstone': cmd_wrightstone(args)
    except RuntimeError as exc:
        # save_and_backup 的安全错误统一在此转成友好提示(不再抛 Traceback)
        msg = {
            'game_running': '检测到游戏正在运行,无法安全写入存档!\n'
                            '       请先完全退出游戏(含 Steam 云同步)后再修改。',
            'write_failed': '写入失败(存档可能被游戏占用或被其他程序锁定)。',
        }.get(str(exc), str(exc))
        print(f'[错误] {msg}')
        sys.exit(2)

if __name__ == '__main__':
    main()
