# -*- coding: utf-8 -*-
"""
Build copy-only Chinese patch files into ./output and ./output_taiwan.

This script reads original source files from ./src_file/DBOZero and writes the
generated patch files to local output folders. It does not read or modify the
live game directory.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

sys.dont_write_bytecode = True

import console_color
import install_hanhua
import lang0_gbk_patch
import tbl_utf16_patch


class OutputError(RuntimeError):
    pass


def tool_dir() -> Path:
    return Path(__file__).resolve().parent


def default_source_dir() -> Path:
    return tool_dir() / "src_file"


def ensure_inside_tool(path: Path) -> Path:
    root = tool_dir().resolve()
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise OutputError(f"Output path must be inside tool folder: {resolved}") from exc
    return resolved


def require_source_layout(source_dir: Path) -> None:
    root = source_dir / "DBOZero"
    required = [root / "pack" / "lang0.pak"]
    required.extend(root / "pack" / name for name in tbl_utf16_patch.TBL_FILES)
    required.extend(root / "localize" / "Taiwan" / "language" / name for name in install_hanhua.LOCALIZATION_FILES)
    for path in required:
        if not path.is_file():
            raise OutputError(f"Missing required source file: {path}")


def write_user_readme(out_dir: Path) -> None:
    text = """DBOZ 简中补丁 使用说明

安装：
1. 关闭游戏和启动器。
2. 自己备份游戏里的 DBOZero 文件夹，至少备份：
   DBOZero\\localize\\Taiwan
   DBOZero\\pack\\lang0.pak
   DBOZero\\pack\\tbl0.pak
   DBOZero\\pack\\tbl1.pak
3. 把本目录里的 DBOZero 文件夹复制到游戏根目录。
4. 提示覆盖时选“是”。
5. 启动器选择 CN 中文。

说明：
- 本补丁不含安装器。
- 本补丁会覆盖 Taiwan 语言文件、lang0.pak、tbl0.pak、tbl1.pak。
- tbl0.pak / tbl1.pak 用于新道具、新称号等 Taiwan/lang0 找不到的文本。
- 出问题就用你自己的备份覆盖回去。
"""
    (out_dir / "使用说明.txt").write_text(text, encoding="utf-8")


def write_taiwan_user_readme(out_dir: Path) -> None:
    text = """DBOZ 台灣繁中補丁 使用說明

安裝：
1. 關閉遊戲和啟動器。
2. 自己備份遊戲裡的 DBOZero 資料夾，至少備份：
   DBOZero\\localize\\Taiwan
   DBOZero\\pack\\lang0.pak
   DBOZero\\pack\\tbl0.pak
   DBOZero\\pack\\tbl1.pak
3. 把本目錄裡的 DBOZero 資料夾複製到遊戲根目錄。
4. 提示覆蓋時選「是」。
5. 啟動器選擇 CN 中文。

說明：
- 本目錄是給台灣 Big5/CP950 環境使用的繁中版。
- local_data.dat、local_sync_data.dat、lang0.pak 使用 CP950 相容字節，避免台灣系統亂碼。
- table_text_all_data.rdf、table_quest_text_data.rdf、tbl0.pak、tbl1.pak 保持遊戲原本的二進制定長格式。
- 出問題就用你自己的備份覆蓋回去。
"""
    (out_dir / "使用说明_台湾繁中.txt").write_text(text, encoding="utf-8")


def transform_lang0_rows(
    rows: list[tuple[str, str]],
    text_transform,
) -> list[tuple[str, str]]:
    return [(key, text_transform(text)) for key, text in rows]


def transform_tbl_rows(
    rows: list[tbl_utf16_patch.TblOverride],
    text_transform,
) -> list[tbl_utf16_patch.TblOverride]:
    return [
        tbl_utf16_patch.TblOverride(row.file_name, row.offset, row.source_text, text_transform(row.translation))
        for row in rows
    ]


def build_output(
    source_dir: Path,
    out_dir: Path,
    clean: bool = True,
    *,
    text_transform=install_hanhua.to_simplified,
    ansi_encoding: str = "gbk",
    readme_writer=write_user_readme,
) -> dict[str, dict[str, int]]:
    source_dir = source_dir.resolve()
    out_dir = ensure_inside_tool(out_dir)
    require_source_layout(source_dir)

    if clean and out_dir.exists():
        shutil.rmtree(out_dir)

    language_dir = out_dir / "DBOZero" / "localize" / "Taiwan" / "language"
    pack_dir = out_dir / "DBOZero" / "pack"
    pack_dir.mkdir(parents=True, exist_ok=True)

    taiwan_overrides = install_hanhua.read_overrides(tool_dir() / "overrides.tsv")
    taiwan_stats = install_hanhua.build_payload(source_dir, language_dir, taiwan_overrides, text_transform, ansi_encoding)

    lang0_rows = lang0_gbk_patch.read_overrides(tool_dir() / "lang0_overrides.tsv")
    lang0_rows = transform_lang0_rows(lang0_rows, text_transform)
    source_lang0 = lang0_gbk_patch.lang0_path(source_dir)
    patched_lang0, lang0_stats = lang0_gbk_patch.patch_lang0_bytes(source_lang0.read_bytes(), lang0_rows, ansi_encoding)
    (pack_dir / "lang0.pak").write_bytes(patched_lang0)

    tbl_rows = tbl_utf16_patch.read_overrides(tool_dir() / "tbl_overrides.tsv")
    tbl_rows = transform_tbl_rows(tbl_rows, text_transform)
    tbl_stats = tbl_utf16_patch.patch_tbl_pack(source_dir, pack_dir, tbl_rows, ansi_encoding)

    readme_writer(out_dir)
    return {
        **taiwan_stats,
        "pack/lang0.pak": lang0_stats,
        **{f"pack/{name}": values for name, values in tbl_stats.items()},
    }


def format_stats(stats: dict[str, dict[str, int]]) -> list[str]:
    lines: list[str] = []
    for name, values in stats.items():
        joined = ", ".join(f"{key}={value}" for key, value in values.items())
        lines.append(f"{name}: {joined}")
    return lines


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="Build DBOZ copy-only Chinese patch output.")
    parser.add_argument("--source-dir", type=Path, default=default_source_dir(), help="Folder containing source DBOZero files. Default: ./src_file")
    parser.add_argument("--out", type=Path, default=tool_dir() / "output")
    parser.add_argument("--taiwan-out", type=Path, default=tool_dir() / "output_taiwan")
    parser.add_argument(
        "--variant",
        choices=("all", "mainland", "taiwan"),
        default="all",
        help="Which output variant to build. Default: all.",
    )
    parser.add_argument("--no-clean", action="store_true", help="Do not delete existing output first.")
    args = parser.parse_args(argv)

    try:
        built: list[tuple[str, Path, dict[str, dict[str, int]]]] = []
        if args.variant in ("all", "mainland"):
            built.append(("mainland", ensure_inside_tool(args.out), build_output(args.source_dir, args.out, clean=not args.no_clean)))
        if args.variant in ("all", "taiwan"):
            built.append((
                "taiwan",
                ensure_inside_tool(args.taiwan_out),
                build_output(
                    args.source_dir,
                    args.taiwan_out,
                    clean=not args.no_clean,
                    text_transform=install_hanhua.to_traditional,
                    ansi_encoding="cp950",
                    readme_writer=write_taiwan_user_readme,
                ),
            ))
    except (install_hanhua.PatchError, lang0_gbk_patch.PatchError, tbl_utf16_patch.PatchError, OutputError) as exc:
        print(console_color.error(f"ERROR: {exc}", sys.stderr), file=sys.stderr)
        return 2

    for label, out_dir, stats in built:
        print(f"Built {label} output: {console_color.path(str(out_dir))}")
        for line in format_stats(stats):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
