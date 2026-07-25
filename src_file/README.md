# src_file：源快照目录

本目录用于存放从你自己安装的游戏中只读同步过来的 **9 个原始资源文件**，
它是扫描和构建的输入。游戏资源文件受版权保护，**不会也不应提交到 Git**。

## 需要哪些文件

相对 `src_file/DBOZero/`：

- `localize/Taiwan/language/local_data.dat`
- `localize/Taiwan/language/local_sync_data.dat`
- `localize/Taiwan/language/table_quest_text_data.rdf`
- `localize/Taiwan/language/table_text_all_data.rdf`
- `pack/gui0.pak`
- `pack/lang0.pak`
- `pack/tbl0.pak`
- `pack/tbl1.pak`
- `pack/tbl2.pak`

## 如何获取

配置好游戏目录后运行：

```powershell
dboc refresh
```

CLI 只会从游戏目录**读取**上述文件并复制到这里，不会写入游戏目录，
也不会复制账号数据、日志、客户端程序或更新缓存。

也可以手动把这 8 个文件按上面的相对路径复制进来（保持目录结构），
之后 `dboc scan` / `dboc build` 即可正常工作。
