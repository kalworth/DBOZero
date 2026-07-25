"""Tests for hanhua_v3.source: layout resolution and read-only snapshot sync."""

from __future__ import annotations

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
