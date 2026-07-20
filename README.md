# DBO Zero 汉化工具链

本仓库使用 v3 表驱动流程，从原始游戏快照生成大陆简中和台湾繁中两套复制式补丁。

## 一键更新

游戏更新后，在仓库根目录运行：

```powershell
python -m hanhua_v3 update
```

该命令会依次完成：

1. 自动提交当前受版本控制内容，建立刷新前恢复点；
2. 从 `E:\DBO Zero 2.0\DBOZero` 只读同步 8 个必要语言/资源包文件；
3. 扫描新版 `lang0.pak`、`tbl0.pak`、`tbl1.pak` 并刷新翻译队列；
4. 仅翻译本次新增且能够可靠处理的词条；
5. 并行构建并验证大陆 GBK 与台湾 CP950 两套输出。

实际游戏目录只作为读取源。CLI 不会写入游戏、复制账号数据、日志、客户端程序或更新缓存。

## 常用命令

```powershell
# 检查 src_file 是否与实际游戏的必要文件一致
python -m hanhua_v3 status

# 只刷新源快照（会先建立 Git 恢复点）
python -m hanhua_v3 refresh

# 只扫描当前 src_file
python -m hanhua_v3 scan

# 只翻译相对 HEAD 新增的队列原文
python -m hanhua_v3 translate --new-since HEAD

# 从较新 Git 状态恢复当前空白译文
python -m hanhua_v3 recover --ref "stash@{1}"

# 构建两套输出；默认并行和增量执行
python -m hanhua_v3 build
```

`python build_output.py` 与 `python -m hanhua_v3.scan` 继续保留为兼容入口，新操作统一使用 `python -m hanhua_v3`。

## 翻译文件

- `data/new_translations.tsv`：新增 `lang0` 和所选 TBL 词条，只填写 `填写中文`。
- `data/translations.tsv`：已接受译文主表，修改现有译文时只改 `zh_cn`。
- `hanhua_v3/glossary.py`：CLI 自动翻译使用的人工校订精确术语。
- `reports/internal/`：扫描与审计产物，不是日常编辑面。

内部标识、纯占位格式和候选噪声不会因“一键更新”被强制汉化。TBL 的 `位置=*` 始终表示按原文进行 UTF-16LE 通配替换，不猜测新版偏移。

## 目录

- `hanhua_v3/`：统一 CLI、扫描、源同步、翻译和 Git 恢复模块。
- `src_file/DBOZero/`：当前版本的 8 个必要原始资源文件。
- `data/`：可维护的翻译主表和日常队列。
- `output/DBOZero/`：大陆简中 GBK 输出。
- `output_taiwan/DBOZero/`：台湾繁中 CP950/Big5 输出。
- `legacy/`：旧解析器和历史资料，仅由 v3 兼容调用。
- `scripts/`：专项恢复工具，不作为日常入口。

## 验证

```powershell
python -m compileall -q build_output.py hanhua_v3
python -m hanhua_v3 status
python -m hanhua_v3 build --force
```

构建完成后应重点检查 `pack/lang0.pak`、`pack/tbl0.pak`、`pack/tbl1.pak` 的 `missing` 计数。
