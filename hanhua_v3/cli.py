from __future__ import annotations

import argparse
import csv
import io
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import __version__, batch_translate_queue, scan
from .recover import RecoveryError, recover_from_git
from .source import (
    DEFAULT_GAME_DIR,
    DEFAULT_SOURCE_DIR,
    SourceRefreshError,
    compare_source,
    refresh_source,
    resolve_source_dir,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QUEUE = ROOT / "data" / "new_translations.tsv"


class CliError(RuntimeError):
    pass


def git_command(*args: str, capture: bool = False) -> subprocess.CompletedProcess[bytes]:
    command = ["git", "-c", f"safe.directory={ROOT.as_posix()}", *args]
    return subprocess.run(
        command,
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE if capture else None,
        stderr=subprocess.PIPE if capture else None,
    )


def create_checkpoint() -> str:
    try:
        status = git_command("status", "--porcelain", "--untracked-files=no", capture=True).stdout.decode(
            "utf-8", errors="replace"
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CliError("无法检查 Git 状态，已停止源文件刷新") from exc

    message = f"Checkpoint before source refresh {datetime.now():%Y-%m-%d %H:%M:%S}"
    try:
        if status.strip():
            git_command("add", "-u")
            git_command("commit", "-m", message)
        else:
            git_command("commit", "--allow-empty", "-m", message)
        return git_command("rev-parse", "--short", "HEAD", capture=True).stdout.decode("ascii").strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise CliError("无法创建刷新前 Git 恢复点，未读取实际游戏目录") from exc


def queue_keys_from_rows(rows: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {
        ((row.get("文件") or "").strip(), (row.get("原文") or "").strip())
        for row in rows
        if (row.get("文件") or "").strip() and (row.get("原文") or "").strip()
    }


def read_queue_rows(path: Path = DEFAULT_QUEUE) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter="\t"))


def read_git_queue_rows(ref: str) -> list[dict[str, str]]:
    try:
        payload = git_command("show", f"{ref}:data/new_translations.tsv", capture=True).stdout.decode("utf-8-sig")
    except (OSError, subprocess.CalledProcessError, UnicodeDecodeError) as exc:
        raise CliError(f"无法从 Git 引用读取翻译队列：{ref}") from exc
    return list(csv.DictReader(io.StringIO(payload), delimiter="\t"))


def print_refresh_results(results) -> None:
    changed = sum(result.changed for result in results)
    print(f"源文件同步完成：changed={changed}, unchanged={len(results) - changed}")
    for result in results:
        state = "更新" if result.changed else "一致"
        print(f"  [{state}] {result.relative_path.as_posix()} ({result.size} bytes)")


def run_refresh(args: argparse.Namespace, *, checkpoint: bool = True) -> int:
    if checkpoint:
        commit = create_checkpoint()
        print(f"刷新前 Git 恢复点：{commit}")
    results = refresh_source(args.game_dir, args.source_dir)
    print_refresh_results(results)
    return 0


def run_scan(args: argparse.Namespace) -> int:
    return scan.main(
        [
            "--source-dir",
            str(args.source_dir),
            "--data-dir",
            str(ROOT / "data"),
            "--report-dir",
            str(ROOT / "reports"),
        ]
    )


def run_translate(args: argparse.Namespace, only_keys: set[tuple[str, str]] | None = None) -> int:
    if args.new_since:
        old_keys = queue_keys_from_rows(read_git_queue_rows(args.new_since))
        current_keys = queue_keys_from_rows(read_queue_rows(args.queue))
        only_keys = current_keys - old_keys
        print(f"相对 {args.new_since} 的新增原文：{len(only_keys)}")

    stats = batch_translate_queue.translate_queue(
        queue_path=args.queue,
        out_path=args.queue,
        translations_path=ROOT / "data" / "translations.tsv",
        fill_all=args.fill_all,
        replace_existing=args.replace_existing,
        ignore_existing_map=args.ignore_existing_map,
        only_keys=only_keys,
    )
    print(f"翻译完成：selected={stats.selected}, filled={stats.filled}, empty_after={stats.empty_after}")
    print(f"复用现有译文：{stats.reused_existing}")
    print(f"翻译队列：{args.queue}")
    return 0


def run_recover(args: argparse.Namespace) -> int:
    stats = recover_from_git(args.refs, dry_run=args.dry_run)
    print(f"Git 参考：{', '.join(stats.references)}")
    print(f"恢复队列译文：{stats.queue_filled}")
    print(f"恢复主表译文：{stats.master_added}")
    print(f"当前源中不存在：{stats.missing_current_source}")
    print(f"历史译法冲突：{stats.conflicts}（按参数顺序保留第一个）")
    if args.dry_run:
        print("dry-run：未写入文件")
    return 0


def run_build(args: argparse.Namespace) -> int:
    import build_output

    build_args = [
        "--source-dir",
        str(args.source_dir),
        "--variant",
        args.variant,
    ]
    if args.force:
        build_args.append("--force")
    if args.no_parallel:
        build_args.append("--no-parallel")
    return build_output.main(build_args)


def run_update(args: argparse.Namespace) -> int:
    previous_keys = queue_keys_from_rows(read_queue_rows(args.queue))
    commit = create_checkpoint()
    print(f"刷新前 Git 恢复点：{commit}")

    print("\n[1/4] 同步实际游戏源文件")
    print_refresh_results(refresh_source(args.game_dir, args.source_dir))

    print("\n[2/4] 扫描新版词条")
    run_scan(args)
    current_keys = queue_keys_from_rows(read_queue_rows(args.queue))
    new_keys = current_keys - previous_keys
    print(f"本次新增原文：{len(new_keys)}")

    if args.recover_refs:
        print("\n[历史恢复] 回填 Git 中仍匹配当前源的译文")
        recovery = recover_from_git(args.recover_refs)
        print(f"恢复队列译文：{recovery.queue_filled}，恢复主表译文：{recovery.master_added}")

    print("\n[3/4] 翻译本次新增词条")
    translate_args = argparse.Namespace(
        queue=args.queue,
        fill_all=args.fill_all,
        replace_existing=False,
        ignore_existing_map=False,
        new_since=None,
    )
    run_translate(translate_args, only_keys=None if args.translate_all else new_keys)

    print("\n[4/4] 构建并验证补丁")
    return run_build(args)


def run_status(args: argparse.Namespace) -> int:
    rows = read_queue_rows(args.queue)
    filled = sum(bool((row.get("填写中文") or "").strip()) for row in rows)
    print(f"翻译队列：total={len(rows)}, filled={filled}, empty={len(rows) - filled}")
    try:
        comparison = compare_source(args.game_dir, args.source_dir)
    except SourceRefreshError as exc:
        print(f"实际游戏源检查失败：{exc}")
        return 2
    different = [result for result in comparison if result.changed]
    print(f"源快照：different={len(different)}, matched={len(comparison) - len(different)}")
    for result in different:
        print(f"  [不同] {result.relative_path.as_posix()}")
    return 1 if different else 0


def add_source_args(parser: argparse.ArgumentParser, *, include_game: bool) -> None:
    parser.add_argument(
        "--source-dir",
        type=Path,
        default=DEFAULT_SOURCE_DIR,
        help="src_file 或 src_file/DBOZero 路径",
    )
    if include_game:
        parser.add_argument(
            "--game-dir",
            type=Path,
            default=DEFAULT_GAME_DIR,
            help="实际游戏 DBOZero 目录，仅作为只读同步源",
        )


def add_build_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--variant", choices=("all", "mainland", "taiwan"), default="all")
    parser.add_argument("--force", action="store_true", help="强制清理并重建输出")
    parser.add_argument("--no-parallel", action="store_true", help="顺序构建大陆与台湾版本")


def add_translate_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    parser.add_argument("--fill-all", action="store_true", help="对选中行启用兜底词组翻译")
    parser.add_argument("--replace-existing", action="store_true", help="重新生成已填写行")
    parser.add_argument("--ignore-existing-map", action="store_true", help="不复用 translations.tsv 同原文译法")
    parser.add_argument("--new-since", help="只翻译相对指定 Git 引用新增的原文，例如 HEAD")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="dboc", description="DBO Zero 汉化 v3 统一命令行工具")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)

    update = subparsers.add_parser("update", help="一键完成恢复点、源刷新、扫描、翻译和构建")
    add_source_args(update, include_game=True)
    add_build_args(update)
    update.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    update.add_argument("--fill-all", action="store_true", help="为本次新增词条启用兜底词组翻译")
    update.add_argument("--translate-all", action="store_true", help="处理全部空白队列，而非仅本次新增")
    update.add_argument("--recover-ref", action="append", dest="recover_refs", default=[], help="扫描后从指定 Git 引用恢复译文，可重复")
    update.set_defaults(handler=run_update)

    refresh = subparsers.add_parser("refresh", help="建立恢复点并从实际游戏目录刷新必要源文件")
    add_source_args(refresh, include_game=True)
    refresh.set_defaults(handler=run_refresh)

    scan_parser = subparsers.add_parser("scan", help="扫描 src_file 并刷新翻译队列")
    add_source_args(scan_parser, include_game=False)
    scan_parser.set_defaults(handler=run_scan)

    translate = subparsers.add_parser("translate", help="批量填写可确定的队列译文")
    add_translate_args(translate)
    translate.set_defaults(handler=run_translate)

    recover = subparsers.add_parser("recover", help="从 Git 历史状态结构化恢复丢失译文")
    recover.add_argument("--ref", action="append", dest="refs", required=True, help="Git 引用，可重复并按优先级排列")
    recover.add_argument("--dry-run", action="store_true", help="只统计，不写入 TSV")
    recover.set_defaults(handler=run_recover)

    build = subparsers.add_parser("build", help="构建大陆简中和台湾繁中补丁")
    add_source_args(build, include_game=False)
    add_build_args(build)
    build.set_defaults(handler=run_build)

    status = subparsers.add_parser("status", help="检查翻译队列和实际游戏源快照差异")
    add_source_args(status, include_game=True)
    status.add_argument("--queue", type=Path, default=DEFAULT_QUEUE)
    status.set_defaults(handler=run_status)
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    args = build_parser().parse_args(argv)
    if hasattr(args, "source_dir"):
        args.source_dir = resolve_source_dir(args.source_dir)
    try:
        return args.handler(args)
    except (CliError, RecoveryError, SourceRefreshError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
