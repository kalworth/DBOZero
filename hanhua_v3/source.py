from __future__ import annotations

import hashlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_GAME_DIR = Path(r"E:\DBO Zero 2.0\DBOZero")
DEFAULT_SOURCE_DIR = ROOT / "src_file" / "DBOZero"

# Only copy original assets consumed by scan.py and build_output.py. Runtime
# logs, account data, executables, caches, and updater files never belong here.
SOURCE_FILES = (
    Path("localize/Taiwan/language/local_data.dat"),
    Path("localize/Taiwan/language/local_sync_data.dat"),
    Path("localize/Taiwan/language/table_quest_text_data.rdf"),
    Path("localize/Taiwan/language/table_text_all_data.rdf"),
    Path("pack/gui0.pak"),
    Path("pack/lang0.pak"),
    Path("pack/tbl0.pak"),
    Path("pack/tbl1.pak"),
)


class SourceRefreshError(RuntimeError):
    pass


@dataclass(frozen=True)
class SourceFileResult:
    relative_path: Path
    changed: bool
    size: int
    sha256: str


def resolve_game_dir(path: Path) -> Path:
    path = path.expanduser().resolve()
    if (path / "pack" / "lang0.pak").is_file():
        return path
    nested = path / "DBOZero"
    if (nested / "pack" / "lang0.pak").is_file():
        return nested
    raise SourceRefreshError(f"找不到游戏资源目录：{path}")


def resolve_source_dir(path: Path) -> Path:
    path = path.expanduser().resolve()
    if path.name.casefold() == "dbozero":
        return path
    return path / "DBOZero"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_layout(root: Path) -> None:
    missing = [str(relative) for relative in SOURCE_FILES if not (root / relative).is_file()]
    if missing:
        raise SourceRefreshError("缺少必要源文件：" + ", ".join(missing))


def refresh_source(game_dir: Path, source_dir: Path = DEFAULT_SOURCE_DIR) -> list[SourceFileResult]:
    game_root = resolve_game_dir(game_dir)
    source_root = resolve_source_dir(source_dir)
    validate_layout(game_root)

    results: list[SourceFileResult] = []
    for relative in SOURCE_FILES:
        source = game_root / relative
        target = source_root / relative
        source_hash = sha256_file(source)
        changed = not target.is_file() or sha256_file(target) != source_hash
        if changed:
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(f".{target.name}.refresh.tmp")
            try:
                shutil.copy2(source, temporary)
                if sha256_file(temporary) != source_hash:
                    raise SourceRefreshError(f"复制校验失败：{relative}")
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
        results.append(SourceFileResult(relative, changed, source.stat().st_size, source_hash))

    validate_layout(source_root)
    return results


def compare_source(game_dir: Path, source_dir: Path = DEFAULT_SOURCE_DIR) -> list[SourceFileResult]:
    game_root = resolve_game_dir(game_dir)
    source_root = resolve_source_dir(source_dir)
    validate_layout(game_root)

    results: list[SourceFileResult] = []
    for relative in SOURCE_FILES:
        live_file = game_root / relative
        live_hash = sha256_file(live_file)
        snapshot_file = source_root / relative
        changed = not snapshot_file.is_file() or sha256_file(snapshot_file) != live_hash
        results.append(SourceFileResult(relative, changed, live_file.stat().st_size, live_hash))
    return results
