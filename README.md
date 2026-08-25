# GBFR 存档修改器（自用）

《碧蓝幻想：Relink》本地存档修改工具。无需打开游戏即可修改主存档
`SaveData1.dat`（默认 `%LOCALAPPDATA%\GBFR\Saved\SaveGames\SaveData1.dat`）。

> 本仓库为个人自用仓库，用于两台电脑之间同步代码、持续迭代。

## 功能

- 物品数量修改、生成合法因子（自动校验副词条组合合法性）
- 角色因子配装 / 卸下、召唤石、配装方案保存恢复
- **召唤石自定义（v1.3）**：DLC 2.0 召唤石背包编辑 —— 种类/主加护/副词条/等级/阶级
  全部以**真实名称**显示与修改（哈希已逆向为名称目录），支持新增、换种类、4 槽装备
- 上限突破（Overmastery）、小钳蟹收集、武器祝福（Wrightstone）生成
- 每次写入自动备份原档 + 重算 xxHash64 校验和，支持 `--dry-run` 预览
- GUI（tkinter）为暗色主题界面（参照 GBFR PE Patch Tool 风格）：彩色分级日志、
  底部状态栏、程序化图标、关于对话框、窗口几何记忆、快捷键（F5 刷新 / Ctrl+B 备份 /
  Ctrl+O 选择存档 / Ctrl+H 关于）

## 目录结构

```
save_tool/                      # 全部核心代码与数据（详见 save_tool/README.md）
  gbfr_gui.py                   # GUI 入口（tkinter）
  gbfr_cheat_tool.py            # CLI 核心，全部修改逻辑
  gbfr_crab_tool.py / gbfr_sigil_tool.py / gbfr_datai.py
  catalog*.json / gem_legality.json / chara_names.json ...   # 运行数据
  build_catalogs.py / extract_tables.py                      # 数据构建脚本
  gbfr-save-editor/             # 上游参考项目（仅依赖其 core 模块）
docs/                           # 开发文档
extracted/                      # 逆向提取的参考数据
```

`_*.py / _*.msg / _*.txt` 为开发期逆向脚本与中间产物，非运行时依赖，保留作开发参考。

## 快速开始

```bash
cd save_tool
python gbfr_cheat_tool.py items list            # CLI 用法
python gbfr_gui.py                              # 打开图形界面
python -m PyInstaller GBFR存档修改器.spec --clean  # 打包 exe
```

依赖：Python 3.10+、`msgpack`；打包需 `pyinstaller`。详见 `save_tool/README.md`。

## 重要提醒

- **修改存档前请完全退出游戏（含 Steam 云同步）**，避免存档被覆盖。
- 工具每次写入会自动生成备份（`SaveData1.dat.<操作>_<时间戳>`），回退即改回原名。
- 本项目包含从游戏本体提取的数据表与逆向成果，请勿公开分发。
