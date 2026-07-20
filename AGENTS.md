# Repository Guidelines

## Tips

Answer questions in Chinese, and address me as "老大" before every answer.

## Current Workflow

This workspace builds a copy-only DBO Zero Chinese patch from `src_file/DBOZero`. Never write to the live game directory `E:\DBO Zero 2.0`. The only allowed live-directory read is an explicit `dboc refresh` or `dboc update`, which copies the required original assets into `src_file/DBOZero`.

## CLI Usage Documentation

- The canonical `dboc` installation, command, option, and example documentation is in the repository-root `README.md`.
- Read `README.md` before operating the CLI. Use `dboc --help` or `dboc <command> --help` for the live argument reference.
- When a CLI command, option, default, or workflow changes, update `README.md` in the same change. Keep `AGENTS.md` focused on repository constraints and safety rules rather than duplicating the complete user guide.

Use the unified v3 CLI:

- Install or refresh the `dboc` command with `python -m hanhua_v3.install_cli`; uninstall only the command wrapper with `python -m hanhua_v3.install_cli --uninstall`.

- `dboc update`: creates a Git checkpoint, refreshes source assets, scans, translates new rows, and builds both outputs.
- `dboc status`: compares the 8 required source assets with the live game directory without modifying either location.
- `dboc refresh`: creates a Git checkpoint and refreshes only the 8 required source assets.
- `dboc scan`: refreshes discovery data and translation queues from `src_file/DBOZero`.
- `dboc recover --ref "stash@{n}"`: fills current blank translations from Git history using exact keys and unambiguous source-text fallback.
- `dboc build`: builds both outputs in parallel by default.
- `data/translations.tsv`: accepted translation master table. Edit `zh_cn` only when changing an existing accepted translation.
- `data/new_translations.tsv`: daily queue for new `lang0.pak` and selected TBL translations. Fill only `填写中文`.
- `reports/internal/tbl_internal_candidates.tsv`: full internal TBL candidate audit. Do not treat it as the daily translation table.
- `reports/what_to_do_next.md`: short human workflow guide.
- `build_output.py`: builds both user-facing outputs.

The old `python -m hanhua_v3`, `build_output.py`, and `python -m hanhua_v3.scan` entrypoints remain compatible, but daily work should use `dboc`.

Build from this directory:

```powershell
dboc build
```

Expected outputs:

- `output/DBOZero`: mainland Simplified Chinese, GBK-oriented.
- `output_taiwan/DBOZero`: Taiwan Traditional Chinese, CP950/Big5-oriented.

## Source And Output Boundaries

- `src_file/DBOZero/` is the source snapshot. It should contain original files from the current game version, not a previously patched game folder.
- `output/`, `output_taiwan/`, and `release/` are generated deliverables.
- `legacy/` contains archived tools, old TSV files, and historical reference data. Do not restart old override workflows unless explicitly asked.
- `reports/internal/` contains generated discovery/audit tables. Keep them out of the daily editing surface.
- Generated game-facing files must not be converted to UTF-8 Chinese text.

## Translation Table Rules

- Keep TSV files tab-separated. Do not align columns with spaces.
- In `data/new_translations.tsv`, fill only `填写中文`; leave IDs, source text, and reference columns intact.
- `位置=*` in TBL rows means a UTF-16LE wildcard translation by source text. Do not replace it with a guessed offset.
- Candidate/discovery files are not proof that a string is visible in game. Promote or translate rows based on user selection, screenshots, or clear text relevance.
- `tbl0.pak` values `AzureRenegade` and `BurningRenegade` are internal title-effect tokens and must remain byte-for-byte untranslated. Their spaced `tbl1.pak` display names may be translated.

## Text Source Priority Rules

- Default to `local_data.dat` / `local_sync_data.dat` first for short normal UI labels, attribute names, status labels, and other non-rich-text UI strings.
- Use `lang0.pak` or TBL for rich text, long text, message popups, system messages, and newly added UI/TBL text whose runtime source is known to be `lang0` or `tbl`.
- Do not let old `local_data.dat` wording override new element terminology. Water / Fire / Ice / Lightning / Wind style new attribute content should keep the current `lang0` / new-content translations unless runtime evidence proves another source is used.
- If a visible short label still comes from `lang0.pak` even though the same key exists in `local_data.dat`, first verify the runtime source from screenshots or output bytes. Only then add a narrowly scoped `lang0` special case.
- The validated pattern for cramped `lang0.pak` status labels is fixed-width unquoted replacement: replace the whole quoted field, for example `"STR"`, with a same-length value such as `力量 ` in GBK. This is allowed only when the output file size is unchanged and the game has been tested to accept the unquoted value.
- Do not use this unquoted `lang0` pattern as a general replacement strategy. Keep it limited to proven short labels such as the six base status stats unless a new case is separately tested.

## Encoding And Pack Rules

- `local_data.dat` and `local_sync_data.dat` are generated as ANSI game files, not UTF-8.
- `lang0.pak` uses fixed raw-byte text patching and is the only surface with a hard original-field-length limit. If a `lang0.pak` translation is too long after GBK/CP950 conversion, shorten it.
- Do not apply the `lang0.pak` length rule to Taiwan/RDF or TBL work.
- TBL strings are fixed-size binary fields. Keep stored length prefixes unchanged; shorter UTF-16LE replacements must be padded with NUL bytes (`00 00`), never visible spaces (`20 00`).
- Do not manually shorten TBL names just to match old text length unless the patcher reports a real unsafe row.

## Source Refresh Rules

When `src_file/DBOZero` is replaced with a newer game snapshot:

1. Run `dboc update`; it creates the required local Git checkpoint automatically and includes tracked `data/new_translations.tsv` changes.
2. If running steps manually, create the checkpoint before `dboc scan`.
3. Run `dboc build` after manual translation work.
4. Check build stats, especially `pack/lang0.pak`, `pack/tbl0.pak`, and `pack/tbl1.pak` `missing` counts.
5. If fixed TBL rows move, use the current v3 data first. Only use legacy relocation scripts when explicitly needed for old override recovery.

## Validation

The active v3 validation baseline is:

```powershell
python -m py_compile build_output.py hanhua_v3\scan.py
dboc status
dboc scan
dboc build
```

Do not use `legacy/tools/validate_output.py` as the default v3 validation gate.

## Code Style

Use Python 3 and the standard library unless there is a clear reason to add a dependency. Keep changes scoped to the v3 workflow unless the user asks for legacy recovery.
