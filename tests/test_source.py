"""Tests for hanhua_v3.source: layout resolution and read-only snapshot sync."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from hanhua_v3 import source


def make_game_dir(root: Path, *, nested: bool = False) -> Path:
    game_root = root / "game"
    dbo = game_root / "DBOZero" if nested else game_root
    for relative in source.SOURCE_FILES:
        target = dbo / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(f"content-of-{relative.name}".encode("ascii"))
    return game_root


def test_resolve_game_dir_direct(tmp_path: Path) -> None:
    game_root = make_game_dir(tmp_path)
    assert source.resolve_game_dir(game_root) == game_root.resolve()


def test_resolve_game_dir_nested_dbozero(tmp_path: Path) -> None:
    game_root = make_game_dir(tmp_path, nested=True)
    assert source.resolve_game_dir(game_root) == (game_root / "DBOZero").resolve()


def test_resolve_game_dir_missing(tmp_path: Path) -> None:
    with pytest.raises(source.SourceRefreshError):
        source.resolve_game_dir(tmp_path / "nothing")


def test_resolve_source_dir_appends_dbozero(tmp_path: Path) -> None:
    assert source.resolve_source_dir(tmp_path / "src_file") == (tmp_path / "src_file" / "DBOZero").resolve()
    dbo = tmp_path / "src_file" / "DBOZero"
    assert source.resolve_source_dir(dbo) == dbo.resolve()


def test_validate_layout_reports_missing(tmp_path: Path) -> None:
    with pytest.raises(source.SourceRefreshError) as excinfo:
        source.validate_layout(tmp_path)
    assert "lang0.pak" in str(excinfo.value)


def test_refresh_source_copies_and_detects_changes(tmp_path: Path) -> None:
    game_root = make_game_dir(tmp_path)
    source_dir = tmp_path / "src_file"

    results = source.refresh_source(game_root, source_dir)
    assert all(result.changed for result in results)
    for relative in source.SOURCE_FILES:
        copied = source_dir / "DBOZero" / relative
        assert copied.read_bytes() == f"content-of-{relative.name}".encode("ascii")

    second = source.refresh_source(game_root, source_dir)
    assert not any(result.changed for result in second)

    lang0 = game_root / "pack" / "lang0.pak"
    lang0.write_bytes(b"new-content")
    third = source.refresh_source(game_root, source_dir)
    changed = {result.relative_path for result in third if result.changed}
    assert changed == {Path("pack/lang0.pak")}


def test_compare_source_flags_differences(tmp_path: Path) -> None:
    game_root = make_game_dir(tmp_path)
    source_dir = tmp_path / "src_file"
    source.refresh_source(game_root, source_dir)

    assert not any(result.changed for result in source.compare_source(game_root, source_dir))

    (game_root / "pack" / "tbl0.pak").write_bytes(b"changed")
    changed = {result.relative_path for result in source.compare_source(game_root, source_dir) if result.changed}
    assert changed == {Path("pack/tbl0.pak")}


def make_variant_copy(game_root: Path, variant: Path, *relatives: Path) -> Path:
    for relative in relatives:
        target = variant / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(game_root / relative, target)
    return variant


def test_detect_patched_source_flags_output_identical_file(tmp_path: Path) -> None:
    game_root = make_game_dir(tmp_path)
    variant = make_variant_copy(game_root, tmp_path / "output" / "DBOZero", Path("pack/lang0.pak"))
    warnings = source.detect_patched_source(game_root, variant_dirs=(variant,))
    assert any("lang0.pak" in warning for warning in warnings)


def test_detect_patched_source_ignores_passthrough_gui0(tmp_path: Path) -> None:
    game_root = make_game_dir(tmp_path)
    variant = make_variant_copy(game_root, tmp_path / "output" / "DBOZero", *source.SOURCE_FILES)
    warnings = source.detect_patched_source(game_root, variant_dirs=(variant,))
    assert warnings
    assert not any("gui0.pak" in warning for warning in warnings)


def test_detect_patched_source_utf8_fallback(tmp_path: Path) -> None:
    game_root = make_game_dir(tmp_path)
    assert source.detect_patched_source(game_root, variant_dirs=()) == []
    (game_root / "pack" / "lang0.pak").write_bytes("账号创建成功".encode("gbk"))
    warnings = source.detect_patched_source(game_root, variant_dirs=())
    assert any("lang0.pak" in warning for warning in warnings)


def test_refresh_source_refuses_patched_game(tmp_path: Path) -> None:
    game_root = make_game_dir(tmp_path)
    variant = make_variant_copy(game_root, tmp_path / "output" / "DBOZero", Path("pack/tbl0.pak"))
    try:
        source.refresh_source(game_root, tmp_path / "src_file", variant_dirs=(variant,))
    except source.SourceRefreshError as exc:
        assert "tbl0.pak" in str(exc)
    else:
        raise AssertionError("refresh should refuse patched game files")
