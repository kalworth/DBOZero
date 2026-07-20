# hanhua_v3 模块说明

`hanhua_v3` 是当前汉化工具链的统一实现层。仓库根目录运行：

```powershell
dboc --help
```

模块职责：

- `cli.py`：`update/refresh/scan/translate/recover/build/status` 命令编排。
- `install_cli.py`：在当前 Python 的 Scripts 目录安装或卸载 `dboc.cmd`。
- `source.py`：从实际游戏目录只读同步 8 个必要源资源，并逐文件校验 SHA-256。
- `scan.py`：扫描 Taiwan、lang0 和 TBL，刷新当前目录与日常翻译队列。
- `batch_translate_queue.py`：保留格式、占位符和内部标识边界的批量翻译器。
- `glossary.py`：人工校订的精确译名。
- `recover.py`：从 Git 历史 TSV 恢复仍匹配当前源的译文，不恢复旧代码或旧 TBL 偏移。

日常只编辑：

- `data/new_translations.tsv` 的 `填写中文`；
- `data/translations.tsv` 的 `zh_cn`。

`reports/internal/` 仅用于搜索和审计。
