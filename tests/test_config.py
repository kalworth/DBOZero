"""Tests for hanhua_v3.config: parsing, saving, and game-dir resolution order."""

from __future__ import annotations

from pathlib import Path

import pytest

from hanhua_v3 import config


def test_load_config_missing_file(tmp_path: Path) -> None:
    assert config.load_config(tmp_path / "nope.toml") == {}


def test_load_config_parses_quoted_values(tmp_path: Path) -> None:
    path = tmp_path / "dboc.toml"
    path.write_text(
        '# comment\n'
        'game_dir = "E:\\\\DBO Zero 2.0\\\\DBOZero"\n'
        '\n'
        'other = "值"\n',
        encoding="utf-8",
    )
    values = config.load_config(path)
    assert values["game_dir"] == "E:\\DBO Zero 2.0\\DBOZero"
    assert values["other"] == "值"


def test_load_config_rejects_bad_line(tmp_path: Path) -> None:
    path = tmp_path / "dboc.toml"
    path.write_text("game_dir = unquoted\n", encoding="utf-8")
    with pytest.raises(config.ConfigError):
        config.load_config(path)


def test_save_game_dir_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "dboc.toml"
    target = tmp_path / "game"
    target.mkdir()
    config.save_game_dir(target, path)
    assert config.load_config(path)["game_dir"] == str(target.resolve())


def test_resolve_game_dir_cli_arg_wins(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cli_value = tmp_path / "from_cli"
    monkeypatch.setenv(config.ENV_GAME_DIR, str(tmp_path / "from_env"))
    assert config.resolve_game_dir(cli_value, config_path=tmp_path / "none.toml") == cli_value


def test_resolve_game_dir_env_beats_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    env_value = tmp_path / "from_env"
    cfg = tmp_path / "dboc.toml"
    cfg.write_text(f'game_dir = "{str(tmp_path / "from_cfg").replace(chr(92), chr(92) * 2)}"\n', encoding="utf-8")
    monkeypatch.setenv(config.ENV_GAME_DIR, str(env_value))
    assert config.resolve_game_dir(None, config_path=cfg) == env_value


def test_resolve_game_dir_config_beats_autodetect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg_value = tmp_path / "from_cfg"
    cfg = tmp_path / "dboc.toml"
    cfg.write_text(f'game_dir = "{str(cfg_value).replace(chr(92), chr(92) * 2)}"\n', encoding="utf-8")
    monkeypatch.delenv(config.ENV_GAME_DIR, raising=False)
    monkeypatch.setattr(config, "autodetect_game_dir", lambda: tmp_path / "detected")
    assert config.resolve_game_dir(None, config_path=cfg) == cfg_value


def test_resolve_game_dir_autodetect_used(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    detected = tmp_path / "detected"
    monkeypatch.delenv(config.ENV_GAME_DIR, raising=False)
    monkeypatch.setattr(config, "autodetect_game_dir", lambda: detected)
    assert config.resolve_game_dir(None, config_path=tmp_path / "none.toml") == detected


def test_resolve_game_dir_raises_with_guidance(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(config.ENV_GAME_DIR, raising=False)
    monkeypatch.setattr(config, "autodetect_game_dir", lambda: None)
    with pytest.raises(config.ConfigError) as excinfo:
        config.resolve_game_dir(None, config_path=tmp_path / "none.toml")
    message = str(excinfo.value)
    assert "dboc config --game-dir" in message
    assert config.ENV_GAME_DIR in message
