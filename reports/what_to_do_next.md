# 翻译工作说明

老大，以后做翻译只看这两个文件。

## 1. 补新内容

打开：`data/new_translations.tsv`

只填这一列：

- `填写中文`: 你只填这一列

其他列只是参考：

- `来源`: UI 表示 lang0，TBL 表示 tbl0.pak / tbl1.pak
- `文件`: 来源文件
- `位置`: key 或 offset
- `原文`: 游戏原文
- `参考译文`: 旧资料里找到的参考译法
- `长度状态`: `too_long` 表示可能放不进固定长度字段

当前待填行数：28302

这个表包含 UI/lang0 和 TBL 待翻译内容。TBL 行很多，建议优先按 `来源`、`文件` 或关键词筛选。

## 2. 改旧翻译

打开：`data/translations.tsv`

只改这一列：

- `zh_cn`: 当前中文译文

TBL 里为了长度把“那美克”写成“那美”这种情况可以保留。

短普通 UI、属性名、状态名优先改 `local_data.dat` 对应行。富文本、长文本、消息弹窗、新增 UI/TBL 文本继续按实际来源改 `lang0.pak` 或 TBL。

有一种例外：如果截图证明某个短标签实际读的是 `lang0.pak`，而 `local_data.dat` 改了也无效，可以做很窄的 `lang0` 特判。已验证可用的范式是状态栏 6 个基础属性：把 `"STR"` 这类 5 字节字段替换成 `力量 ` 这种同长度无引号值，保证 `lang0.pak` 文件大小不变。不要把这个当成通用写法，必须逐项验证。

## 3. 生成补丁

翻译改完后，在当前目录运行：

```powershell
python build_output.py
```

它会重新生成：

- `output/DBOZero`: 大陆简中 GBK 版
- `output_taiwan/DBOZero`: 台湾繁中 CP950 版

发简中补丁就打包 `output`。

发台湾繁中补丁就打包 `output_taiwan`。

不要把 `src_file`、`data`、`legacy`、`reports` 一起发出去。

## 4. 检查结果

生成后至少确认这些文件存在：

- `output/DBOZero/localize/Taiwan/language/local_data.dat`
- `output/DBOZero/pack/lang0.pak`
- `output/DBOZero/pack/tbl0.pak`
- `output/DBOZero/pack/tbl1.pak`
- `output_taiwan/DBOZero/localize/Taiwan/language/local_data.dat`
- `output_taiwan/DBOZero/pack/lang0.pak`
- `output_taiwan/DBOZero/pack/tbl0.pak`
- `output_taiwan/DBOZero/pack/tbl1.pak`

`build_output.py` 只读 `src_file/DBOZero`，不会动真实游戏目录。

## 5. 其他文件

平时不用看。

`reports/internal/` 里是工具内部生成物，平时不用看。
