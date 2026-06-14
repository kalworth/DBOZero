# 翻译工作说明

老大，以后做翻译只看这两个文件。

## 1. 补新内容

打开：`data/待翻译_新增内容.tsv`

只填这一列：

- `填写中文`: 你只填这一列

其他列只是参考：

- `来源`: UI 表示 lang0
- `文件`: 来源文件
- `位置`: key 或 offset
- `原文`: 游戏原文
- `参考译文`: 旧资料里找到的参考译法
- `长度状态`: `too_long` 表示可能放不进固定长度字段

当前待填行数：4230

这个表现在只放 UI/lang0 待翻译内容，避免 TBL 几万行候选干扰你。

## 2. 改旧翻译

打开：`data/translations.tsv`

只改这一列：

- `zh_cn`: 当前中文译文

TBL 里为了长度把“那美克”写成“那美”这种情况可以保留。

## 3. 其他文件

不用看。

`data/catalog_current.tsv`、`data/candidates_unified.tsv`、`data/workbench.tsv`、`reports/internal/` 都是工具内部生成物。
