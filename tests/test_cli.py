"""Parser-level tests for the dboc CLI."""

from __future__ import annotations

from pathlib import Path

import pytest

from hanhua_v3 import cli


def test_parser_requires_subcommand() -> None:
    with pytest.raises(SystemExit):
        cli.build_parser().parse_args([])


def test_build_defaults() -> None:
    args = cli.build_parser().parse_args(["build"])
    assert args.variant == "all"
    assert args.force is False
    assert args.no_parallel is False
    assert not hasattr(args, "game_dir")


def test_build_variant_and_flags() -> None:
    args = cli.build_parser().parse_args(["build", "--variant", "taiwan", "--force", "--no-parallel"])
    assert args.variant == "taiwan"
    assert args.force is True
    assert args.no_parallel is True


def test_game_dir_optional_on_refresh() -> None:
    args = cli.build_parser().parse_args(["refresh"])
    assert args.game_dir is None
    args = cli.build_parser().parse_args(["refresh", "--game-dir", "D:/games/DBO Zero 2.0"])
    assert args.game_dir == Path("D:/games/DBO Zero 2.0")


def test_config_subcommand() -> None:
    args = cli.build_parser().parse_args(["config", "--show"])
    assert args.show is True
    assert args.game_dir is None


def test_version_exits_zero(capsys: pytest.CaptureFixture) -> None:
    with pytest.raises(SystemExit) as excinfo:
        cli.main(["--version"])
    assert excinfo.value.code == 0
    assert "dboc" in capsys.readouterr().out
