# GBFR(碧蓝幻想:Relink)伤害公式解包笔记 — v2.0.5 / DLC 无尽黄昏

> 本文档记录从游戏本体(`granblue_fantasy_relink.exe` + `data.i`)解码伤害公式、敌人数值、难度体系与各类机制的**完整步骤**与**知识沉淀**。
> 方法原则:**以检查游戏源代码为主**(exe 字符串/RTTI 符号、数据表、行为树/FSM、官方文本哈希反解),网络社区实测仅作辅助标注。

---

## 一、环境与前置

| 项 | 值 |
|---|---|
| 游戏 | Granblue Fantasy: Relink,版本 v2.0.5(DLC 无尽黄昏 Endless Ragnarok),2026-08-29 更新 |
| 安装路径 | `I:\STEAM\steamapps\common\Granblue Fantasy Relink` |
| 主程序 | `granblue_fantasy_relink.exe`(123 MB,native x64,自研引擎) |
| 资源包 | `data.i`(索引,FlatBuffers)+ `data.0~data.11`(内容) |
| 上游参考 | [Nenkai/GBFRDataTools](https://github.com/Nenkai/GBFRDataTools)(headers 列定义、ids.txt 哈希表、文件清单) |
| 哈希 | `gbfr_hash` = XXHash32Custom(表内所有字符串 ID 的 u32 哈希),实现见上游 `hashing.py` |
| 依赖 | Python 3.10+、lz4、msgpack、openpyxl |

---

## 二、解码步骤(完整流程)

### 步骤 1 — 数据索引解析
- 用 FlatBuffers 最小读取器解析 `data.i`,得到 `archive_file_hashes`(40.8 万文件哈希)、`file_to_chunk` 映射、`chunks`(每个文件在 data.X 中的偏移/大小)。
- 文件定位 = `gbfr_file_hash(路径小写)`(XXHash64 seed 0,大端)二分查找。

### 步骤 2 — 表头(列定义)获取与解析
- 从 GBFRDataTools master 抓取全部 `.headers` 文件(约 48 个伤害相关表 + 补充表)。
- headers 语法:`add_column|名|类型[|0xNN]`、`padding`、`include`、版本门控 `set_min_version/set_max_version/reset_*`。
- **必须完整复刻 C# 读取器的版本门控语义**:`(版本 < min) 或 (版本 > max) 时跳过该列`;版本号解析为 4 段数值元组(如 `2.0.0.2`)。
- 关键坑:行内 `//` 注释需在 `|` 切分后剥除;`raw_string` 的长度来自第三个参数(如 `0x10`)。

### 步骤 3 — 数据表提取
- tbl 二进制:`int64 行数` 位于偏移 0,随后是定长行。
- 按 headers 解码为 JSON(列名 → 值),保存到 `_dmg_data/json/`。
- 校验:行大小整除、数值合理性;与旧版本提取结果交叉核对(攻击力 L45=1400 在 2.0.4/2.0.5 一致)。
- 提取的表:skill_status(因子数值,6320 行)、skill(因子说明)、gem(因子组合)、weapon_status/chara_status/enemy_status、limit_bonus_param、quest_difficulty/quest_rank、status(状态)、ability(技能)、endlessmode_difficulty/enemy_adjust、constant 等。

### 步骤 4 — 战斗曲线解包
- `curve/battle/*.f-curve.msg`(msgpack):`{Count, Array: [[插值类型, x, y, 入切线, 出切线], ...]}`。
- 插值类型:`FlatToNext`(保持)、`Linear`(线性)、`Smooth/SmoothSide`(Hermite,切线×Δx)。
- 得到 热血(stamina)/背水(enmity)/坚守(garrison)/不屈(sturdy)/Link时间(linktime) 的 HP 比例→加成系数曲线,并生成每 1% 稠密表。
- 例:热血满血系数 1.0、50% 血 0.25;背水 0 血 1.0、50% 血 0.34。

### 步骤 5 — 哈希体系破解(gbfr_hash)
- 表内所有 Key/引用为 u32 哈希 = `gbfr_hash(字符串)`(XXHash32Custom,**大小写敏感**)。
- 反解对象:
  - 敌人: `gbfr_hash("EM7700")` = 1571541002 等(对照 enemy_status Key 验证);
  - 难度: `gbfr_hash("DIF_340")` = quest_difficulty Key(**难度名哈希即 quest_difficulty 主键**,由此打通 难度→敌人等级);
  - 参数键: 暴力破解 `ENDLESS_ENEMY_ADJUST_{grade}_{enemy}_{tier}`(grade 1-5 × enemy 1-3 × tier 1-5,53/53 全部命中);
  - 文本: `gbfr_hash(文本ID)` 反查 text.msg 得到官方说明文字(因子/技能/任务说明)。

### 步骤 6 — 官方文本反解(因子/技能语义)
- 提取 `system/table/text/{en,cs}/*.msg`(35 个文件、33K 条文本,msgpack:`rows_[].column_{id_hash_, subid_hash_, text_}`)。
- skill.tbl 的 Name/Summary/Explain 哈希 → 文本,获得每个因子的官方说明(如追击"X% chance to trigger Supplementary DMG"、热血"Boosts ATK by a max of +70% at 100% HP")。
- 由此**以代码层文本判定乘区归属**:凡"ATK +%"进攻击力区;凡"DMG Dealt +%"进伤害乘区;凡"Supplementary DMG"进追击系统。

### 步骤 7 — exe 字符串/RTTI 分析
- 从 `granblue_fantasy_relink.exe` 提取 ASCII(≥6 字符)与 UTF-16(≥4 字符)字符串(约 60 万条)。
- 关键符号命中:
  - 伤害上限系统:`PlayerDamageLimitParameter`、`ChainBurstATKRate_FullChain/3Chain/2Chain`、`skillBoardDamageRateUp/Down`、`SetEnemyDamageRate`;
  - 追加伤害系统:`EmAddDamageParam`、`addDamageParamPower_`、`addDamage1stParam_/2ndParam_`、`addDamageLimitBonusStatusRate_`、`weakElementAddDamageRate_`;
  - 敌人减伤:`damageCutRate_`、`powerDamageCutRate_`、`hellPowerDamageCutRate_`、`barrierDamageCutRate_`、`firstMeleeDamageCutRate_`、`GuardDamageCutRate/GuardBreakDamageCutRate`;
  - 世界(EM8300):`Em8300ReflectLaser`、`shot_reflected_laser`、`shot_just_reflected_laser`、`justiceRate_/justiceMaxRate_`、`reflectedLaserDamageRate_`、`Em8300Param::InfinityBuffParam/BuffParam/SetTarotParam`;
  - 无尽黄昏:`ENDLESS_{:d}`、`ENDLESS_ENEMY_ADJUST_{0:d}_{1:d}_{2:d}`、`CheckUnlockInfinity`、`IsQuestInfinity`。

### 步骤 8 — 任务 → Boss 映射(placement 场景文件)
- 任务实体配置在 `layout/p*/placement_multi_<questId>.scene.msg`(msgpack 场景树)。
- 从中提取 EmXXXX 行为引用 → 该任务出现的敌人(如 40b313 → Em7700 路西法)。
- ER DLC 任务在 `quest/ex/<id>/baseinfo.msg`,经典任务在 `quest/<id>/BaseInfo.msg`;提取 difficultyHash_ → 难度名。
- 难度名 → quest_difficulty 行 → `EnemyLevelUltimate`(敌人等级)。
- **由此定位 Infinity(无限)档 = 40b3xx 系列,DIF_340/350 → 敌人等级 340/350。**

### 步骤 9 — 难度体系破解
- `quest_difficulty.tbl`:Key = 难度名哈希;`EnemyLevelUltimate` = 该难度的敌人等级(低档 20~100,中档 200~280,高档 300~350,封顶 400~500 未知难度名)。
- `endlessmode_difficulty.tbl`:无尽黄昏模式 5 档(敌 Lv 20/50/90-110/180-200/210-230,推荐战力 1500~30000)。
- `endlessmode_enemy_adjust.tbl`:53 条 `(grade, enemy, tier)` HP/ATK 倍率(HP ×1.0~3.0,ATK ×1.0~1.65)。

### 步骤 10 — 数值计算与汇总
- 敌人某等级 HP/ATK = enemy_status 表中该敌人两个相邻等级行线性插值。
- 关卡怪物血量 = 任务难度对应的敌人等级下该怪物的 HP/ATK。
- 输出:多工作表 Excel + 本笔记。

---

## 三、关键知识总结

### 3.1 哈希体系
| 用途 | 方法 |
|---|---|
| 表内字符串 ID | `gbfr_hash(str)`(XXHash32Custom,种子自定义,大小写敏感,u32) |
| 存档文件路径 | `gbfr_file_hash(path)`(XXHash64 seed 0,大端 u64,路径小写) |
| 文本 ID ↔ 内容 | `gbfr_hash("TXT_...")` 反查 text.msg |
| 难度 ↔ 敌人等级 | `gbfr_hash("DIF_340")` = quest_difficulty.Key → EnemyLevelUltimate |
| 参数键 | `gbfr_hash("ENDLESS_ENEMY_ADJUST_3_2_4")` 等格式化串 |

### 3.2 伤害公式(DLC 2.0)
```
实际伤害 = min(可造成伤害, 基础上限×(1+上限up)) × OD缩放 × 上限外增伤
可造成伤害 = 面板攻击力 × (1+攻击up)(1+防御down)(1-攻击down)(1-防御up)(1-白盾)
             × 部位/暴击倍率 × 弱点倍率 × Π(1+非面板乘算) × (1+Σ加算) × 招式倍率 × (1+动作易伤) × 浮动
上限外增伤 = (1+属性弱点) × (1+Σ造成伤害up) + 0.5 × buff增伤
buff增伤 = max{ min[(1+Σ攻up)(1+Σ防down)(1+强壮)(1+逆境), 2]×(1-攻down)(1-防up)(1-白盾) - 1, 0 }
```
- 上限检测:可造成伤害未达上限时 buff 增伤 = 0;OD 缩放 < 1 的 Boss 恒为 0。

### 3.3 攻击力乘区(问题一)
- 暴君/热血/背水/攻击力因子/穷寇心/刀上舞/浪迹天涯 官方文本均为"ATK +X%",全部**加算**进同一面板攻击力乘区 `(1+Σ攻击力%)`。
- 面板攻击力 = (角色基础 + 武器 + 收集 + 天赋/上限突破) × (1+Σ攻击力%)。
- 与"伤害 UP"(连击加成等)区分:后者走可造成伤害公式的伤害乘区。

### 3.4 追击系统(问题二)
- 本质:独立 addDamage 段,`追击伤害 = 主伤害 × Σ各来源追击伤害%`,概率触发,独立显示、独立于上限。
- 来源:
  - 追击因子:追击率 12→100% + 追击伤害 20%;追击率多因子加算至 100% 上限;
  - 斯巴达:追击伤害 20%,触发率按基础 HP 独立判定(HP≥80000→100%);
  - 狂战士 Berserker Echo:追击伤害 20%,触发率按基础 ATK 独立判定(ATK≥25000→100%);
  - 技能追击 buff(塞达/炎帝等被动):tsuigeki 状态(StatusId=7),按技能参数;
  - 守护者的决心:固定 10% 追击 + 15% 上限。
- 结论:**追击伤害% 各来源加算;触发率各自判定(互不覆盖,可同时触发)**。
- 注意区分:穷寇心 Berserker = 攻击+80%(非追击);狂战士 Berserker Echo = 追击(按 ATK 条件)。

### 3.5 世界(EM8300)弹反(问题三)
- 弹反 = 反射(Reflect):`Em8300ReflectLaser`/`shot_reflected_laser`/`justiceRate_`/`reflectedLaserDamageRate_`。
- 减伤:敌人减伤参数类 `damageCutRate_/guardPointDamageCutRate_/powerDamageCutRate_/hellPowerDamageCutRate_/barrierDamageCutRate_/firstMeleeDamageCutRate_`(姿态期间生效,数值为编译常量)。
- 塔罗牌状态:em8300_justice(128)/death(129)/devil(130)/towor(131)/judgment(132),带等级,时长约 100 秒。
- Infinity 专属:`Em8300Param::InfinityBuffParam`;自我攻防:`em8300_atkup(146)/em8300_defdown(147)`。

### 3.6 上限与额外伤害(问题四)
- 攻击 up/防御 down 会被上限机制约束(buff 增伤区的上限检测)。
- 天星之雪(Celestial Aqua, SKILL_324_00)= 对 Break 敌人/连锁中伤害 +15%,属于上限内伤害乘区;不影响独立追击段;受上限截断。
- 追击段只受专属率参数影响(weakElementAddDamageRate_ 等),不被主伤害乘区(如天星之雪)放大。

### 3.7 减伤机制(问题五,保留)
- 玩家基础防御 = 0;受伤 = 怪原伤害 ×(1-攻down)×(1-特防)×(1-防up)×(1-霸体30%)×(1-特减)×(1-减伤%)。
- 减伤乘区:霸体 30% / 专精+浪迹天涯+坚持(同区加算)/ 刚健·坚守(HP 曲线防御+)/ 黑螃蟹 2% / 螃蟹报恩 10%。

### 3.8 Infinity 难度体系
- Infinity = 40b3xx 任务系列,DIF_340(四天王:路西法/别西卜/世界/异型巴哈+伊德)、DIF_350(天元),敌人等级 340/350。
- 敌等级→HP/ATK 见 enemy_status(如路西法 L340 = 11.56 亿 HP / 109,725 ATK)。
- 无尽黄昏档(40a3xx)= DIF_240~330(敌 Lv 240~330);经典档(407xxx)= DIF_150~250。

---

## 四、已知局限
- 招式倍率、伤害上限基数(10000)、暴击浮动、世界弹反减伤精确百分比 = 程序编译常量,字符串无法直接读出(机制由符号确认,数值待实机)。
- 追击率加算至 100%、追击伤害加算 = 社区实测结论(exe 符号仅佐证独立 addDamage 系统)。
- `quest_difficulty` 的 f23/f24、`endlessmode_enemy_adjust` 的 grade/enemy/tier 精确语义待实机确认。
- 旧版(1.x)公式与 2.x 有差异(2.0 起 buff 影响上限),本笔记以 2.0.5 为准。

---

## 五、文件索引
- Excel 交付物:`GBFR伤害公式_v3_代码解包版.xlsx`(27 表:7 张问题/机制表 + 数据参考表)
- 解包中间产物:`_dmg_data/json/*.json`(55+ 表)、`_dmg_data/headers/*.headers`、`_dmg_data/curves/*`、`_dmg_data/web/*`(社区资料)
- 关键脚本:`_dmg_data/extract_tables.py`(表提取+版本门控)、`parse_curves.py`(曲线)、`resolve_names.py`(名称反解)、`extract_exe_strings.py`(exe 字符串)、`build_quest_roster.py`(关卡怪物)、`map_quest_em.py`(任务→Boss)、`build_xlsx3.py`(Excel 生成)
- 网络资料:碧蓝幻想relink吧 voltskyghost《无尽黄昏伤害计算公式解析》(2026-08)、3DM ted1985、游民星空 M_Eve0、escapist 追击/上限详解
