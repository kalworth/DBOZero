# DBO Zero 汉化工具链

从游戏原始资源生成大陆简中（GBK）和台湾繁中（CP950/Big5）两套**复制式**汉化补丁：
构建产物直接覆盖到游戏目录即可生效，不修改游戏程序，不写注册表。

> **免责声明**：本项目是非官方的玩家自制工具，与游戏开发商/运营商无关。
> 仓库不包含任何游戏资源文件；补丁由工具在你本机安装的游戏基础上生成。
> 使用本工具及补丁的风险自负，请先备份游戏目录。

## 只想用汉化补丁的玩家

不需要安装 Python，也不需要 clone 本仓库：

1. 到 [Releases 页面](https://github.com/kalworth/DBOZero/releases)下载最新补丁压缩包（简中或繁中）；
2. 解压，把其中的 `DBOZero` 目录里的内容复制到游戏目录下的 `DBOZero`，覆盖同名文件；
3. 启动游戏。

还原原文：用游戏启动器的文件校验/修复功能，或重新覆盖回你备份的原始文件。

## 想参与翻译或自己构建补丁

### 环境要求

- Windows（游戏本身是 Windows 程序；工具链的纯 Python 部分同样可在 macOS/Linux 运行）
- Python 3.9 或更高版本
- Git
- 一份已安装的 DBO Zero 游戏（用于只读提取原始资源文件）

### 快速开始

```powershell
git clone https://github.com/kalworth/DBOZero.git
cd DBOZero
pip install -e .            # 安装跨平台的 dboc 命令（可编辑安装）
dboc config --game-dir "E:\DBO Zero 2.0"   # 配置一次游戏目录
dboc update                 # 提取源文件 → 扫描 → 翻译新增 → 构建两套补丁
```

游戏目录配置只需做一次，写入仓库根的 `dboc.toml`（已 gitignore）。
不配也可以：CLI 会依次尝试 `DBOC_GAME_DIR` 环境变量和常见安装路径自动探测，
或用 `--game-dir` 参数临时指定。查看当前生效值：`dboc config --show`。

### 翻译入口

只编辑这两个文件：

- `data/new_translations.tsv`：新增词条队列，**只填 `填写中文` 列**；
- `data/translations.tsv`：已接受译文主表，**只改 `zh_cn` 列**。

改完运行 `dboc build` 重新生成补丁：

- `output/DBOZero`：大陆简中 GBK 版；
- `output_taiwan/DBOZero`：台湾繁中 CP950/Big5 版。

翻译必须遵守的规则（编码、长度、来源优先级等）见
[docs/translation-rules.md](docs/translation-rules.md)。

### 常用命令

```powershell
dboc update        # 游戏更新后一键：恢复点 → 同步源 → 扫描 → 翻译新增 → 构建
dboc status        # 对比源快照与本机游戏是否一致
dboc refresh       # 只从游戏目录同步 9 个必要源文件（会先建 Git 恢复点）
dboc scan          # 只扫描 src_file 并刷新翻译队列
dboc translate     # 批量填写可确定的队列译文
dboc build         # 构建两套补丁（默认并行、增量）
dboc config        # 查看/写入游戏目录配置
dboc --help        # 全部命令与参数
```

游戏目录只作为**读取源**。CLI 不会写入游戏目录，也不会复制账号数据、
日志、客户端程序或更新缓存。

## 仓库结构

```
hanhua_v3/     v3 工具链实现（CLI、扫描、翻译、恢复、配置）
  runtime/     构建实际依赖的补丁模块（唯一维护副本）
data/          翻译主表与日常队列（仓库核心资产）
src_file/      源快照目录（游戏资源不入库，用法见其 README）
docs/          翻译规则与开发者文档
output*/       生成的补丁（不入库）
legacy/        归档的旧工具与历史译法资料（tools 内为兼容垫片）
scripts/       专项恢复工具，非日常入口
tests/         单元测试（pytest）
```

更多开发细节（模块职责、验证流程、代码约定）见
[docs/development.md](docs/development.md)。

## License

代码以 [MIT License](LICENSE) 发布。游戏本身的资源与商标归原权利人所有。
