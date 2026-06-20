# Repository Guidelines

## Tips

Answer questions in Chinese, and address me as "老大" before every answer.

## Current Workflow

This workspace builds a copy-only DBO Zero Chinese patch from `src_file/DBOZero`. Do not read from or write to the live game directory `E:\DBO Zero 2.0`.

Use the v3 table-driven workflow:

- `python -m hanhua_v3.scan`: refreshes discovery data and translation queues from `src_file/DBOZero`.
- `data/translations.tsv`: accepted translation master table. Edit `zh_cn` only when changing an existing accepted translation.
- `data/new_translations.tsv`: daily queue for new `lang0.pak` and selected TBL translations. Fill only `填写中文`.
- `reports/internal/tbl_internal_candidates.tsv`: full internal TBL candidate audit. Do not treat it as the daily translation table.
- `reports/what_to_do_next.md`: short human workflow guide.
- `build_output.py`: builds both user-facing outputs.

Build from this directory:

```powershell
python build_output.py
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

## Encoding And Pack Rules

- `local_data.dat` and `local_sync_data.dat` are generated as ANSI game files, not UTF-8.
- `lang0.pak` uses fixed raw-byte text patching and is the only surface with a hard original-field-length limit. If a `lang0.pak` translation is too long after GBK/CP950 conversion, shorten it.
- Do not apply the `lang0.pak` length rule to Taiwan/RDF or TBL work.
- TBL strings are fixed-size binary fields. Keep stored length prefixes unchanged; shorter UTF-16LE replacements must be padded with NUL bytes (`00 00`), never visible spaces (`20 00`).
- Do not manually shorten TBL names just to match old text length unless the patcher reports a real unsafe row.

## Source Refresh Rules

When `src_file/DBOZero` is replaced with a newer game snapshot:

1. Before running `python -m hanhua_v3.scan`, make a local git commit of the current workspace state so rewritten queue files can be restored. This commit must include `data/new_translations.tsv` if it exists.
2. Run `python -m hanhua_v3.scan`.
3. Run `python build_output.py`.
4. Check build stats, especially `pack/lang0.pak`, `pack/tbl0.pak`, and `pack/tbl1.pak` `missing` counts.
5. If fixed TBL rows move, use the current v3 data first. Only use legacy relocation scripts when explicitly needed for old override recovery.

## Validation

The active v3 validation baseline is:

```powershell
python -m py_compile build_output.py hanhua_v3\scan.py
python -m hanhua_v3.scan
python build_output.py
```

Do not use `legacy/tools/validate_output.py` as the default v3 validation gate.

## Code Style

Use Python 3 and the standard library unless there is a clear reason to add a dependency. Keep changes scoped to the v3 workflow unless the user asks for legacy recovery.
