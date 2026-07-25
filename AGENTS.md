# Repository Guidelines

## Tips

Answer questions in Chinese, and address me as "老大" before every answer.

## Current Workflow

This workspace builds a copy-only DBO Zero Chinese patch from `src_file/DBOZero`. Never write to the live game directory. The only allowed live-directory read is an explicit `dboc refresh` or `dboc update`, which copies the required original assets into `src_file/DBOZero`.

## CLI Usage Documentation

- The canonical user-facing documentation is the repository-root `README.md`.
- Translation and build rules live in `docs/translation-rules.md`; module architecture and dev workflow live in `docs/development.md`. Read them before changing translation handling or build logic.
- Use `dboc --help` or `dboc <command> --help` for the live argument reference.
- When a CLI command, option, default, or workflow changes, update `README.md` (and `docs/` when relevant) in the same change. Keep `AGENTS.md` focused on repository constraints and safety rules.

Use the unified v3 CLI:

- Install with `pip install -e .` (editable install; the workspace root must stay the repository root). This is the only supported installation path.

- `dboc update`: creates a Git checkpoint, refreshes source assets, scans, translates new rows, and builds both outputs.
- `dboc status`: compares the 8 required source assets with the live game directory without modifying either location.
- `dboc refresh`: creates a Git checkpoint and refreshes only the 8 required source assets.
- `dboc scan`: refreshes discovery data and translation queues from `src_file/DBOZero`.
- `dboc recover --ref "stash@{n}"`: fills current blank translations from Git history using exact keys and unambiguous source-text fallback.
- `dboc build`: builds both outputs in parallel by default.
- `dboc config`: shows or writes the per-machine game directory in `dboc.toml` (gitignored). Resolution order: `--game-dir` > `DBOC_GAME_DIR` env > `dboc.toml` > autodetect. Never hardcode a game path in source code.

The old `python -m hanhua_v3`, `build_output.py`, and `python -m hanhua_v3.scan` entrypoints remain compatible, but daily work should use `dboc`.

Build from this directory:

```powershell
dboc build
```

Expected outputs:

- `output/DBOZero`: mainland Simplified Chinese, GBK-oriented.
- `output_taiwan/DBOZero`: Taiwan Traditional Chinese, CP950/Big5-oriented.

## Source And Output Boundaries

- `src_file/DBOZero/` is the source snapshot, synced read-only from the user's own game install via `dboc refresh`. It contains copyrighted game assets and is **not tracked by Git** — never commit it.
- `dboc.toml` is per-machine local config and is **not tracked by Git**.
- `output/`, `output_taiwan/`, and `release/` are generated deliverables, not tracked.
- `hanhua_v3/runtime/` holds the actively maintained patching modules (moved from `legacy/tools`). Edit them there; the same-named files under `legacy/tools/` are compatibility shims only.
- `legacy/` otherwise contains archived tools, old TSV files, and historical reference data. Do not restart old override workflows unless explicitly asked.
- `reports/internal/` contains generated discovery/audit tables. Keep them out of the daily editing surface.
- Generated game-facing files must not be converted to UTF-8 Chinese text.

## Translation Rules

The full translation-table, text-source-priority, and encoding/pack rules are in `docs/translation-rules.md`. They are normative for any change touching `data/` or the build pipeline.

## Validation

The active v3 validation baseline is:

```powershell
python -m compileall -q build_output.py hanhua_v3
pytest
dboc status
dboc build
```

Do not use `legacy/tools/validate_output.py` as the default v3 validation gate. CI mirrors these checks (compile, pytest, CLI smoke) on Windows and Ubuntu.

## Code Style

Use Python 3 and the standard library unless there is a clear reason to add a dependency. Tests live in `tests/` and use pytest. Keep changes scoped to the v3 workflow unless the user asks for legacy recovery.
