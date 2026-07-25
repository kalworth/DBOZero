# 开发者文档

面向想修改工具链本身或深入了解流程的开发者。日常翻译规则见
`docs/translation-rules.md`。

## 模块结构

- `hanhua_v3/cli.py`：`update/refresh/scan/translate/recover/build/status/config` 命令编排。
- `hanhua_v3/config.py`：本机配置（`dboc.toml`）、环境变量与游戏目录自动探测。
- `hanhua_v3/source.py`：从游戏目录只读同步 9 个必要源资源，逐文件 SHA-256 校验。
- `hanhua_v3/scan.py`：扫描 Taiwan、lang0 和 TBL，刷新翻译队列与内部审计表。
- `hanhua_v3/batch_translate_queue.py`：保留格式、占位符和内部标识边界的批量翻译器。
- `hanhua_v3/glossary.py`：人工校订的精确术语。
- `hanhua_v3/recover.py`：从 Git 历史 TSV 恢复仍匹配当前源的译文。
- `hanhua_v3/policy.py`：扫描与构建共用的源保留策略（如 TBL 内部令牌黑名单）。
- `hanhua_v3/runtime/`：构建/扫描实际依赖的补丁模块（`install_hanhua`、`lang0_gbk_patch`、`tbl_utf16_patch`、`console_color`、`auto_translate_new_source`）。它们来自 `legacy/tools`，此处是唯一维护副本；`legacy/tools/` 只保留兼容垫片。
- `build_output.py`：构建大陆简中 / 台湾繁中两套输出的入口，由 `dboc build` 调用。

## 安装与运行

```powershell
pip install -e .        # 提供跨平台 dboc 命令（可编辑安装，工作区即仓库）
dboc config --game-dir "E:\DBO Zero 2.0"   # 或依赖自动探测 / DBOC_GAME_DIR
dboc update
```

注意：工具以仓库根目录为工作区（`data/`、`src_file/`、`output/` 都是相对它的），
因此只支持**可编辑安装**（`pip install -e .`）或在仓库根目录直接
`python -m hanhua_v3`。非可编辑的全局安装会让工作区定位失效。

## 工作区目录

- `data/`：翻译主表与日常队列（入库，核心资产）。
- `src_file/DBOZero/`：源快照，从本机游戏只读同步（不入库，见 `src_file/README.md`）。
- `output/`、`output_taiwan/`：生成的补丁（不入库）。
- `release/`：本地打包的历史发布（不入库）。
- `reports/internal/`：扫描与审计产物（不入库）。
- `legacy/`：归档的旧工具、旧 TSV 和历史参考资料；`legacy/translations/`、`legacy/candidates/` 仍被扫描器作为历史译法来源读取。
- `scripts/`：专项恢复工具，不是日常入口。

## 验证

改动代码后按以下顺序自检：

```powershell
python -m compileall -q build_output.py hanhua_v3
pytest
dboc status
dboc build
```

构建完成后重点检查 `pack/lang0.pak`、`pack/tbl0.pak`、`pack/tbl1.pak` 的
`missing` 计数（应为 0）。不要把 `legacy/tools/validate_output.py` 当作
v3 的验证门槛。

CI（`.github/workflows/ci.yml`）在 Windows 和 Ubuntu、Python 3.9/3.12 上
执行编译检查、单元测试和 CLI 冒烟测试。

## 代码约定

- Python 3，只用标准库；新增依赖需要有明确理由并在 `pyproject.toml` 声明。
- 测试统一放 `tests/`，用 pytest。
- 改动保持最小化， scoped 在 v3 流程内；legacy 只用于历史恢复。
