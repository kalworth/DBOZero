from __future__ import annotations

import argparse
import sys
import sysconfig
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MARKER = "DBOC_MANAGED_WRAPPER"


def default_scripts_dir() -> Path:
    value = sysconfig.get_path("scripts")
    if not value:
        raise RuntimeError("无法确定当前 Python 的 Scripts 目录")
    return Path(value)


def wrapper_text() -> str:
    return "\r\n".join(
        [
            "@echo off",
            f"rem {MARKER}",
            "setlocal",
            f'set "PYTHONPATH={ROOT};%PYTHONPATH%"',
            f'"{Path(sys.executable).resolve()}" -m hanhua_v3 %*',
            "exit /b %errorlevel%",
            "",
        ]
    )


def install(scripts_dir: Path, *, force: bool) -> Path:
    scripts_dir = scripts_dir.expanduser().resolve()
    scripts_dir.mkdir(parents=True, exist_ok=True)
    target = scripts_dir / "dboc.cmd"
    if target.exists():
        existing = target.read_text(encoding="utf-8", errors="replace")
        if MARKER not in existing and not force:
            raise RuntimeError(f"拒绝覆盖非本工具创建的命令：{target}；确认后可使用 --force")
    with target.open("w", encoding="utf-8", newline="") as handle:
        handle.write(wrapper_text())
    return target


def uninstall(scripts_dir: Path) -> Path:
    target = scripts_dir.expanduser().resolve() / "dboc.cmd"
    if not target.exists():
        return target
    existing = target.read_text(encoding="utf-8", errors="replace")
    if MARKER not in existing:
        raise RuntimeError(f"拒绝删除非本工具创建的命令：{target}")
    target.unlink()
    return target


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="安装或卸载 dboc Windows 命令入口")
    parser.add_argument("--scripts-dir", type=Path, default=default_scripts_dir())
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--force", action="store_true", help="允许覆盖已有的非托管 dboc.cmd")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.uninstall:
            target = uninstall(args.scripts_dir)
            print(f"已卸载 dboc：{target}")
        else:
            target = install(args.scripts_dir, force=args.force)
            print(f"已安装 dboc：{target}")
            print(f"工作区：{ROOT}")
        return 0
    except (OSError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
