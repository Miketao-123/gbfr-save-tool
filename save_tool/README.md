# GBFR 简易作弊器(本地存档修改)

一个基于 Python 的《碧蓝幻想：Relink》存档修改工具,无需打开游戏即可修改 `SaveData1.dat`。
所有修改都会**自动备份原档 + 重算存档校验和**,写入前可先用 `--dry-run` 预览。

## 角色名支持(v1.1+)

所有需要角色的命令/界面(角色、配装、上限突破、召唤石、因子"装备给")都可以直接用**游戏内角色名**,
也兼容原来的 `PLxxxx` 代码与 `0x` 哈希。角色名取自游戏本体文本表(中英双语):

| 输入 | 示例 | 说明 |
|---|---|---|
| 中文名 | `欧根`、`卡塔莉娜` | 优先精确匹配,支持包含匹配 |
| 英文名 | `Eugen`、`Katalina` | 不区分大小写 |
| 下拉格式 | `欧根 (PL0500)` | GUI 下拉框选择后的值,可直接用 |
| PL 代码 | `PL0500`、`0500` | 原格式,继续兼容 |
| 0x 哈希 | `0x079DF0CC` | 高级用法 |

列表输出统一显示为 `欧根 (Eugen) [PL0500]` 形式。
说明:部分预留角色槽(PL2000、PL3000~PL3900)在本版游戏文本中无名,仍显示代码。

## 环境

- 需要 Python 3.10+ 与 `msgpack` 库(`pip install msgpack`)
- 修改前请**完全退出游戏**(含 Steam 云同步),避免存档被覆盖

## 命令速览

```
python gbfr_cheat_tool.py [--save 存档路径] <命令>
```

| 命令 | 说明 |
|---|---|
| `items list [关键词]` | 列出物品与数量(支持中文/英文/0x哈希搜索) |
| `items set <物品> <数量>` | 修改物品数量(物品需已存在于存档) |
| `sigils list [关键词]` | 列出因子目录 |
| `sigils add <因子> [--level N] [--secondary 词条] [--equip PLxxxx] [--dry-run]` | **生成合法因子**(自动校验词条组合合法性) |
| `chars list` | 列出装备了因子的角色 |
| `chars sigils <PLxxxx>` | 查看某角色已装备的因子 |
| `chars equip <PLxxxx> <因子槽号或名称>` | 把因子装备到角色 |
| `chars unequip <PLxxxx> <槽号>` | 从角色卸下因子 |
| `chars clear <PLxxxx>` | 卸下该角色全部因子 |
| `summons list` | 列出召唤石 |
| `summons set <槽号> [--chara PLxxxx] [--level N]` | 修改召唤石(装备角色/等级) |
| `loadout list / save <名> <PLxxxx> / restore <名>` | 保存/恢复某角色的因子配装方案 |
| `wrightstone list` | 列出 4 种武器祝福类型 |
| `wrightstone traits [关键词]` | 列出祝福可用词条(71 种,存档实测合法) |
| `wrightstone add <祝福> --traits "词条:等级,词条:等级,词条:等级"` | **生成武器祝福**(3 词条,等级 0-20) |

### 武器祝福(生成)

写入位置:存档 ItemManager 槽位 50000+（2102=物品哈希, 2103=序列号, 词条在
140000000+(槽-50000)×100 的 3 条词条位）。4 种祝福类型:恐惧/活力/强化/封印
(对应 Dread/Vitality/Fortification/Sequestration Wrightstone)。

```bash
# 生成一个恐惧祝福,词条为 暴击率20 + 挑衅15 + 攻击力10
python gbfr_cheat_tool.py wrightstone add 恐惧祝福 --traits "暴击率:20,挑衅:15,攻击力:10"

# 只预览不写入
python gbfr_cheat_tool.py wrightstone add 活力祝福 --traits "体力:20" --dry-run
```

- 词条池 = 存档中祝福上实测出现过的词条(71 种),保证组合合法;
- 等级上限 20(游戏实测),不填等级默认 20;
- 生成的祝福进入背包(武器祝福槽),游戏内给武器装上即可;
- 不指定词条时只写入该祝福类型的默认词条。

### 装备因子上限(防闪退保护)

游戏每个角色**默认最多装备 12 个因子**,第 13 格需要天赋盘"因子栏位解锁"(效果 0x7B727910) 点亮,
**超过上限会闪退**。工具在 `sigils add --equip`、`chars equip`、配装恢复时自动检查:

- 已装数 ≥ 上限 → 拒绝并提示"已装备 X/12 个因子,无法再装";
- 已点亮"因子栏位解锁"的角色上限为 13;
- 装备时自动把 2707 标志规范化为装备行格式(低 2 位 = 2)。

### 装备登记(角色 1403 装备列表)

游戏判定"因子已装备"不仅看 2706(归属哈希),还要求把因子的 **2702 序列号**登记进该角色的
**1403 装备列表(13 格)** —— 只写 2706 的话游戏装备界面**不会显示**该因子。
工具在装备时自动登记、卸下时自动注销。若旧版工具写入的因子在游戏里不显示,用新版工具
对该槽位重新执行一次 `chars equip <角色> <槽号>` 即可补登记。
| `overmastery list <PLxxxx>` | 查看角色 4 条上限突破(效果名/数值/哈希) |
| `overmastery set <PLxxxx> <槽0-3> <效果> <数值0-1023>` | 设置单条上限突破(1023=满值) |
| `overmastery clear <PLxxxx> <槽0-3>` | 清空单条上限突破 |

### 上限突破数值说明

存档值 1607 是 **0~1023 的内部刻度**,映射规则(玩家实测 + 游戏 `limit_bonus_param.tbl`):

- **星级 = floor(log2(存档值)) + 1**,临界点在 2 的幂:64→7⭐、128→8⭐、256→9⭐、512→10⭐
- **显示值 = 该星级的档位值**(下表);512 = 10⭐ = 满档
- 存档值 512~1023 是超出满档的改档区,线性延伸:**1023 → 满档×4(实测普攻伤害上限 20%→80%)**

| 属性 | 7⭐ | 8⭐ | 9⭐ | 10⭐(满档=512) | 1023 |
|---|---|---|---|---|---|
| 暴击率 / 技能伤害 / 奥义伤害 / 连锁爆发伤害 | 10% | 12% | 16% | 20% | 80% |
| 普攻/技能/奥义伤害上限、治疗上限 | 10% | 12% | 16% | 20% | 80% |
| 攻击力 | 600 | 700 | 800 | 1000 点 | ~4000 点 |
| 体力 | 1000 | 1200 | 1600 | 2000 点 | ~8000 点 |
| 昏厥力 | 10 | 12 | 16 | 20 点 | ~80 点 |

工具输出会给出「显示值(含星级)」和「存档值/1023」,与游戏内界面一致。
| `crab [--wee N] [--dark N] [--statue] [--count 20]` | 小钳蟹功能:改普通/漆黑小钳蟹数量、漆黑蟹像=1、完成收集任务 |

## 示例

```bash
# 查看物品
python gbfr_cheat_tool.py items list 漆黑

# 把漆黑小钳蟹改成 999
python gbfr_cheat_tool.py items set 漆黑小钳蟹 999

# 查看蟹类因子
python gbfr_cheat_tool.py sigils list 蟹

# 生成满级可怕的漆黑钳蟹因子(无副词条)
python gbfr_cheat_tool.py sigils add 可怕的漆黑钳蟹因子 --level 20

# 生成刀上舞V+ 并配一个合法副词条"攻击力",直接装备到主角
python gbfr_cheat_tool.py sigils add "Glass Cannon V+" --secondary 攻击力 --equip PL0000

# 预览(不写入)
python gbfr_cheat_tool.py sigils add 可怕的漆黑钳蟹因子 --dry-run

# 查看主角的配装
python gbfr_cheat_tool.py chars sigils PL0000

# 保存主角配装为方案,之后随时恢复
python gbfr_cheat_tool.py loadout save 我的输出配装 PL0000
python gbfr_cheat_tool.py loadout restore 我的输出配装

# 上限突破:查看/设置
python gbfr_cheat_tool.py overmastery list PL0000
python gbfr_cheat_tool.py overmastery set PL0000 0 攻击力 1023
python gbfr_cheat_tool.py overmastery set PL0000 1 暴击率 512

# 小钳蟹:两种小钳蟹数量 + 漆黑蟹像 + 完成任务
python gbfr_cheat_tool.py crab --wee 20 --dark 20 --statue
```

## 合法性说明

- `sigils add` 生成的是**游戏真实存在的因子**:主词条固定为游戏数据中该因子的主词条;
- `--secondary` 指定的副词条会**严格校验**是否在该因子的合法副词条池内,非法组合会被拒绝;
- 合法副词条区间(取自游戏 `system/table` 权威数据 + 游戏内实测,见 `gem_legality.json`):
  1. **固定副词条**:该因子自带 SkillId2(如旧版 `+` 因子的固定词条);
  2. **掉落/抽卡池**:`gem.SkillTypeLotIdForRandom2ndSkill` → `skill_type_lot` → `skill_lot` 展开;
  3. **合成池**:所有 V+(名字含"＋")因子携带的技能 —— 游戏合成 = 选入两个 V+ 因子,
     四个技能(每因子主+副)随机混合取前2 = 全新 V+ 因子(1.3 官方 + 游戏内实测)。
     实测:`昏厥Ⅴ＋` + `天星之炼Ⅴ＋` 有 1/12 概率出"昏厥主+天星之炼副";
     因此任意 V+ 因子都可经合成获得合成池(183 技能,含天星系列/昏厥/刀上舞/攻击力等)中的任意技能。
- 例:`昏厥Ⅴ＋新` 可通过合成获得天星之雪/天星之炼/刀上舞等;`可怕的漆黑钳蟹因子＋` 可经合成获得天星之雪;
- **无+版因子**(如可怕的漆黑钳蟹因子 0x49434696、昏厥Ⅴ)在合成界面灰色不可选,不可经合成加副词条;
- 等级会被限制在该词条的合法上限内。

## 存档备份

每次写入都会在存档同目录生成 `SaveData1.dat.<操作名>_<时间戳>` 备份。
如需回退,把备份文件名改回 `SaveData1.dat` 覆盖即可。

## 数据来源

- 存档解析/校验和:基于开源项目 `xcier/GBFR-Save-Editor`(FlatBuffers + xxHash64)
- 物品/因子/词条目录:从游戏本体 `data.i` 归档提取(gem.tbl / skill.tbl / skill_status.tbl / 文本 .msg)
- 哈希算法:GBFR 自定义 XXHash32(与游戏一致)
- 合成机制:参考 [Nenkai relink-modding wiki](https://nenkai.github.io/relink-modding/resources/re/mechanics/gem_mix/) 与 1.3 官方更新说明
