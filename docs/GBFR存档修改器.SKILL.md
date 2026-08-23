---
name: gbfr-save-editor
description: 了解或修改 GBFR(碧蓝幻想 Relink)存档修改器项目代码、数据文件或打包配置时使用
---

# GBFR 存档修改器 — 项目技能

## 一、项目简介

一个基于 Python 的《碧蓝幻想：Relink》**本地存档修改工具**,无需打开游戏即可修改主存档 `SaveData1.dat`(默认路径 `%LOCALAPPDATA%\GBFR\Saved\SaveGames\SaveData1.dat`)。

核心特性:
- **每次写入自动备份原档 + 重算 xxHash64 校验和**;写入前可用 `--dry-run` 预览,写入后会重新打开存档验证校验和。
- 存档格式:`SaveGameFile` 包装头 + FlatBuffers(`SaveDataBinary`)。校验和位于文件末尾 u32 指向的 10 个 u64 哈希槽,用 `uint:1003`(种子 0x2F1A43EBCD)选择激活槽。
- 功能:物品数量、**生成合法因子**(自动校验副词条组合合法性)、角色因子配装/卸下、召唤石、配装方案保存恢复、上限突破(Overmastery,数值 0–1023)、小钳蟹收集、武器祝福(Wrightstone)生成。
- v1.1+ 起所有涉及角色的命令支持**游戏内角色名**(中文精确/包含匹配、英文不区分大小写),并兼容 `PLxxxx` 代码与 `0x` 哈希;列表输出统一为 `欧根 (Eugen) [PL0500]` 形式。部分预留槽(PL2000、PL3000~PL3900)游戏文本中无名,仍显示 PL 代码。
- 环境:Python 3.10+,依赖 `msgpack`(目录构建脚本用);打包需 PyInstaller。**修改存档前请完全退出游戏(含 Steam 云同步)**,避免被覆盖。

## 二、代码位置与核心文件

全部位于项目根目录下 `save_tool/`。

### 运行时代码(无下划线前缀)

| 文件 | 规模 | 职责 |
|---|---|---|
| `gbfr_gui.py` | ~890 行 | **GUI 入口**(tkinter,标题 "GBFR 存档修改器 v1.1")。是 `gbfr_cheat_tool.py`(导入为 `gct`)的薄封装:`App` 类 + `ttk.Notebook`,每个功能区一个标签页(物品/因子/角色/召唤石/配装方案/上限突破/小钳蟹/祝福);各按钮的 `cmd_*` 方法把输入框组装成 argparse Namespace 后调用对应 `gct.cmd_*(args)`;`LogCapture` 类把 `print` 重定向到界面日志框。含 PyInstaller frozen 兼容(`sys._MEIPASS`) |
| `gbfr_cheat_tool.py` | ~1240 行 | **CLI 核心,全部存档修改逻辑所在**。子命令:`items / sigils / chars / summons / loadout / overmastery / crab / wrightstone`(注册在文件末尾 `main()`)。关键常量:`EMPTY=0x887AE0B0`;id_type 1801/1802(物品哈希/数量)、2701–2707(因子槽)、1701/1702(词条 id/等级);`GEM_SLOT_BASE=30000`、`TRAIT_REC_BASE=120000000`;召唤石 3101/3102/3113。导入时加载全部目录 JSON(CAT/GEMCAT/CHARSCAT/SIGILS_FULL/LEGAL/CHAR_NAMES),并 `sys.path.insert` 引入上游核心 |
| `gbfr_crab_tool.py` | ~215 行 | 独立小工具:改普通/漆黑小钳蟹数量、漆黑蟹像=1(等价完成 DLC 收集链)、置位蟹收集任务(0x290002~0x290015)完成标志。文件头 docstring 有存档格式原理说明 |
| `gbfr_sigil_tool.py` | ~161 行 | 独立小工具:向 GemManager 空槽注入「可怕的漆黑钳蟹因子」(GEEN_301_00,`--plus` 为 +版 GEEN_301_10),演示了完整的"找空槽→写各字段→备份→重算校验和→重开验证"流程 |
| `gbfr_datai.py` | ~155 行 | 游戏数据归档工具:GBFR 自定义 **XXHash64**(`gbfr_file_hash`,对路径小写做 xxh64)实现 + 最小 FlatBuffers 读取器,解析 `data.i` 索引并定位/提取表文件(是逆向工作基础) |
| `README.md` | — | 项目全貌:命令速览、合法性说明、上限突破数值映射表、备份机制、数据来源。**改任何功能前先读它** |

### 数据构建脚本

- `build_catalogs.py`:从提取的 `_cs_text.msg`/`_en_text.msg`(msgpack 文本表)+ `system_table_*.tbl.json` 生成 `catalog.json` / `catalog_gem.json` / `catalog_chars.json`。
- `extract_tables.py`:用 `gbfr_datai.parse_index` + lz4 从游戏 `data.0`/`data.i` 提取并解析 `skill.tbl` / `gem.tbl` / `skill_status.tbl`(含 v2.0.4 列定义,是重新提取表数据的入口)。
- `schema_scan.py`:辅助脚本。

### 上游参考项目(不要整体改动)

`save_tool/gbfr-save-editor/GBFR-Save-Editor-main/` — 开源 "Granblue Fantasy Relink Save Lab"(README 注明存档解析/校验和基于 `xcier/GBFR-Save-Editor`,FlatBuffers + xxHash64)。本工具**只依赖其 `gbfr_editor/core/gbfr_save.py`(GBFRSaveData:open/find/set_first_value/save_over_original 等)与 `hashing.py`(gbfr_hash)**,通过 `sys.path.insert` 引用;其余子目录(ui/cli/data/research/tools/resources)是参考实现,不参与本工具运行。

### 逆向探索文件(下划线前缀 `_*`,~140 个)

`_*.py / _*.msg / _*.txt / _constant.headers` 等是开发期逆向脚本与中间产物(.msg 文本转储、哈希清单、结构探查),**不属于工具运行时依赖**;搜索/理解代码时优先看无下划线前缀的文件,这些可忽略。

## 三、数据文件位置与作用

均位于 `save_tool/`,由本目录构建脚本生成或从游戏本体提取:

| 文件 | 大小级 | 内容 |
|---|---|---|
| `catalog.json` | ~163KB | items/sigils/traits 三张名称表:`hash → {id, en, cn}`(ID 形如 ITEM_XX_YYYY / GEEN_X_Y_Z / SKILL_XX_YY) |
| `catalog_gem.json` | ~187KB | `sigil_info`(每因子的主/副词条哈希、稀有度)+ `trait_info`/`trait_max`(词条名与最大等级,来自 skill_status.tbl) |
| `catalog_sigils_full.json` | **~520KB** | 精简因子目录:V+ 家族保留规则、每个因子的合法副词条池(`allowedSecondaryTraitIds`)、等级约束;含来源审计字段。**不要整体读取,grep 按需查** |
| `gem_legality.json` | **~285KB(1.6万行)** | 游戏权威合法性数据:固定副词条(SkillId2)、掉落/抽卡池(`SkillTypeLotIdForRandom2ndSkill→skill_type_lot→skill_lot`)、合成池(所有"＋"因子技能,183 个)。`sigils add --secondary` 的校验依据。**不要整体读取** |
| `gem_mix_pool.json` | ~8KB | V+ 合成池明细 |
| `catalog_chars.json` | <1KB | 角色哈希 → PLxxxx(PL0000~PL3900) |
| `chara_names.json` | ~2KB | PLxxxx → {cn, en},取自游戏本体 text_chara.msg(中英双语) |
| `wrightstone_traits.json` | ~25KB | 武器祝福可用词条池:存档中实测合法的 71 种 `{internalId, hash, displayName, maxLevel}`;等级上限 20(游戏实测) |
| `system_table_skill.tbl.json` / `_skill_status` / `_gem` | skill_status **~1.9MB** | 从 game data.i 提取的原始表行(JSON);skill_status 不要整体读取 |
| `GBFRDataTools_filelist.txt` | **~20MB**、另两个 GBFRDataTools_*.txt 数百 KB | 上游数据工具的文件清单/ID 清单,**绝不要整体读取**,只 grep |

存档与运行时产物:主存档 `%LOCALAPPDATA%\GBFR\Saved\SaveGames\SaveData1.dat`;每次写入在同目录生成 `SaveData1.dat.<操作名>_<时间戳>` 备份(回退=改回原名覆盖)。配装方案存于源码模式 `save_tool/loadouts/`、打包模式存档同目录 `_loadouts/`(兜底 `%USERPROFILE%\GBFR_SaveTool_loadouts`)。

## 四、常见操作指南

### 1. 如何理解 GUI 代码(`gbfr_gui.py`)
- 它不实现任何修改逻辑,只负责:收集输入(每个字段一个 `tk.StringVar`,在 `App.__init__` 里声明)→ 组装 argparse Namespace → 调用 `gct.cmd_*`(如 `cmd_sigils_add`)→ 用 `LogCapture` 把工具 print 显示到日志框。
- 所以**读懂功能 = 去 `gbfr_cheat_tool.py` 找同名 `cmd_xxx`**;GUI 里只找"哪个按钮调了它、输入来自哪个变量"。
- 角色下拉选项由 `_chara_choices()` 基于 `gct.CHARSCAT` + `CHAR_NAMES` 生成;`frozen`(打包)下资源目录是 `sys._MEIPASS`,可写目录在存档旁——新加数据文件时注意这两处兼容逻辑。

### 2. 如何新增功能(标准流程)
1. **逻辑层**:`gbfr_cheat_tool.py` 里实现 `cmd_xxx(args)`;复用现有原语(`open_save`/`save_and_backup`(自动备份+重算校验和+force 检查游戏是否在运行)/`set_first`/目录查找函数 `find_sigil`、`find_trait`、`find_chara`)。
2. **CLI**:在文件末尾 `main()` 里 `sub.add_parser('xxx')` + 子解析器,并加入分发 dict(照抄相邻命令的写法)。
3. **GUI**:`gbfr_gui.py` 加一个 Notebook 标签页:声明 StringVar → 控件+按钮(`command=self.cmd_xxx`)→ handler 组装 Namespace 调 `gct`。
4. 若引入新数据文件/模块,同步更新 `GBFR存档修改器.spec` 的 `datas` / `hiddenimports`(见下)。
5. 测试:先跑 `--dry-run` 预览;确认输出后真写入,核对"重开校验:通过";再走一遍 GUI。

### 3. 如何打包 exe
- 前置:`pip install pyinstaller msgpack`;在 `save_tool/` 目录执行(工作目录必须是 save_tool,spec 内路径是相对它的):
  ```
  python -m PyInstaller GBFR存档修改器.spec --clean
  ```
- spec 要点:入口脚本 `gbfr_gui.py`;`datas` = 7 个 JSON(catalog.json、catalog_chars/gem/sigils_full、chara_names、gem_legality、gem_mix_pool)+ 上游核心目录 `gbfr-save-editor/GBFR-Save-Editor-main/gbfr_editor/core`(保持原相对路径,与代码里 `sys.path.insert` 的位置一致);`hiddenimports = ['gbfr_cheat_tool','gbfr_save','hashing']`;单文件 EXE、`console=False`(无黑框)、UPX。
- 产物:`dist\GBFR存档修改器.exe`(`build\` 为中间产物可清理)。`dist\GBFR存档修改器_原版备份.exe` 是旧版 exe 的备份,别删错。
- 打包后务必用真实存档跑一遍 GUI(尤其确认 JSON 与上游 core 被正确内嵌——漏数据文件时目录会加载为空 `{}`/None)。

### 4. CLI 命令速览(`python gbfr_cheat_tool.py [--save 路径] <命令>`)
`items list/set` · `sigils list/add`(add: `--level --secondary --equip --dry-run`)· `chars list/sigils/equip/unequip/clear` · `summons list/set` · `loadout list/save/restore` · `wrightstone list/traits/add` · `overmastery list/set/clear` · `crab [--wee N] [--dark N] [--statue]`。详见 `save_tool\README.md`(含上限突破 0~1023→星级映射表与合法性说明)。

## 五、注意事项

- **大文件不要整体读取**:优先 grep/按行区间读。黑名单:`GBFRDataTools_filelist.txt`(~20MB)、`system_table_skill_status.tbl.json`(~1.9MB)、`catalog_sigils_full.json`(520KB)、`gem_legality.json`(285KB);大 `.msg` 转储同理。
- **修改存档前先备份**:工具每次写入自动备份并修校验和,但仍建议保留手动副本;操作前**完全退出游戏(含 Steam 云同步)**——游戏运行时写档可能被覆盖或触发强制写入风险(GUI 有"强制写入"勾选项,慎用)。回退方式:把 `SaveData1.dat.<tag>_<时间戳>` 备份改回 `SaveData1.dat`。
- **防闪退/越界红线**:角色因子装备上限默认 12(点亮天赋盘"因子栏位解锁"效果 0x7B727910 后为 13),**超过会闪退**(工具已自动检查并拒绝);上限突破数值限 0–1023;副词条必须在该因子的合法池内(`gem_legality.json`),等级不超过该词条合法上限。
- **装备因子要双写**:游戏判定"已装备"既看 2706(归属)也要求把因子 2702 序列号登记进角色 1403 装备列表;工具在 equip/unequip 时自动登记/注销——自己改存档逻辑时别漏。
- **上游核心 `gbfr_save.py` / `hashing.py` 是开源已验证代码,不要修改**;需要新行为就扩展本项目的工具层。
- `_*.py/_*.msg/_*.txt`(下划线前缀)是历史逆向产物,不是运行时依赖;构建/打包时也不在 spec 里。
- 游戏更新版本后表结构可能变化(如 `extract_tables.py` 注释的 v2.0.4 列定义),重提数据前先跑 `schema_scan.py` / `gbfr_datai.py` 核对,并用真实存档验证。
