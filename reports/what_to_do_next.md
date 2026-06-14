# What To Do Next

老大，日常不用看全量 catalog。

## 你要改旧翻译

改这个文件：`data/translations.tsv`

常用列：

- `source_text`: 原文
- `zh_cn`: 当前中文，直接改这里
- `status`: 保持 `accepted` 即可；不确定就写 `needs_review`
- `note`: 备注为什么这样翻

TBL 里为了长度把“那美克”写成“那美”这种情况可以保留，不需要为了术语统一强行改。

## 你要补新增翻译

填这个文件：`data/workbench.tsv`

只看这些列：

- `reason`: 为什么需要处理
- `surface`: 属于 lang0 还是 tbl
- `source_text`: 原文
- `current_zh_cn`: 已有旧翻译，没有就空
- `suggested_zh_cn`: 工具给的参考译法
- `zh_cn_new`: 你只需要填这一列
- `fit`: `too_long` 表示可能放不进固定长度字段

填完 `zh_cn_new` 后，后续工具会把这些变更合并进主库。

## 当前优先级

- 先看 `reports/review_conflicts.md`：16 个旧翻译冲突，适合少量人工拍板。
- 再看 `data/workbench.tsv`：62050 行待处理；先筛 `reason = reuse_or_edit_existing_translation`，这些最容易补。
- 暂时不要处理全量 `data/catalog_current.tsv`，它是机器地图。
