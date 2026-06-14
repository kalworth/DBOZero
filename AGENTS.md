# Repository Guidelines

## Tips
Answer questions in Chinese, and address me as "老大" before every answer.

## Project Structure & Module Organization

This repository builds a copy-only DBOZ Simplified Chinese patch. It does not install into the live game folder.

- `build_output.py`: main entry point. Reads source files and writes `output/`.
- `install_hanhua.py`: Taiwan localization builder for `local_data.dat`, `local_sync_data.dat`, and RDF text files.
- `lang0_gbk_patch.py`: raw-byte GBK patcher for `pack/lang0.pak`.
- `tbl_utf16_patch.py`: fixed-size UTF-16LE patcher for `pack/tbl0.pak` and `pack/tbl1.pak`.
- `src_file/DBOZero/`: fixed source snapshot used for building. Do not replace it with a patched game folder.
- `overrides.tsv`: manual Taiwan/RDF text overrides.
- `lang0_overrides.tsv`: manual `lang0.pak` fixed-string overrides.
- `tbl_overrides.tsv`: manual `tbl0.pak` / `tbl1.pak` fixed-string overrides.
- `untranslated.tsv`: lookup list for untranslated or fallback text.
- `taiwan_candidates.tsv`: lookup list for reference-only Taiwan/RDF candidate text.
- `lang0_candidates.tsv`: lookup list for reference-only `lang0.pak` candidate text.
- `tbl_candidates.tsv`: lookup list for reference-only `tbl0.pak` / `tbl1.pak` English text candidates.
- `output/`: generated user-facing patch. Users copy this folder manually.

## Build, Test, and Development Commands

Run the standard build from this directory:

```powershell
python "E:\DBO Zero 2.0_tools\hanhua\build_output.py"
```

The command reads `src_file/DBOZero` and regenerates `output/DBOZero`. It must not read or write `E:\DBO Zero 2.0`.

Useful checks:

```powershell
Select-String -Encoding Default -Path "output\DBOZero\localize\Taiwan\language\local_data.dat" -Pattern "後","於","伺服器"
```

Use this to spot common Traditional Chinese remnants after a build.

## Coding Style & Naming Conventions

Use Python 3 with standard-library code only unless there is a clear reason to add a dependency. Keep functions small and purpose-specific. Use `snake_case` for functions and variables, and uppercase names for constants such as `TAIWAN_SIMPLIFY_FIXUPS`.

TSV files must use real tab separators. Do not align columns with spaces. For four-column overrides, the final column is the output text.

## Testing Guidelines

There is no formal test suite. Validate changes by running `build_output.py` and checking the printed stats. Expected successful output includes all four Taiwan files plus `pack/lang0.pak`, `pack/tbl0.pak`, and `pack/tbl1.pak`.

When editing text conversion, verify both:

- `output\DBOZero\localize\Taiwan\language`
- `output\DBOZero\pack\lang0.pak`
- `output\DBOZero\pack\tbl0.pak`
- `output\DBOZero\pack\tbl1.pak`

Do in-game testing only after manually copying `output/DBOZero` over a backed-up game folder.

## Commit & Pull Request Guidelines

This folder is not currently a git repository. If version control is added, use concise imperative commit messages, for example `Add Taiwan fixup replacements` or `Update lang0 overrides`.

Pull requests should describe the changed files, the build command used, key build stats, and any in-game screens or text verified.

## Agent-Specific Instructions

Do not modify the live game directory. Keep development source files under `src_file/DBOZero`, and keep generated deliverables under `output/`. Prefer fixing broad Taiwan Simplified Chinese issues in `install_hanhua.py`; use `overrides.tsv` for specific Taiwan/RDF text entries, `lang0_overrides.tsv` for `lang0.pak`, and `tbl_overrides.tsv` for `tbl0.pak` / `tbl1.pak`.

When the user replaces `src_file/DBOZero` with files from a newer game version, do not assume the old patch is globally unusable. The most likely breakage is that fixed offsets in `tbl_overrides.tsv` no longer point at the same strings in the refreshed `pack/tbl0.pak` and `pack/tbl1.pak`. First run the standard build and check `pack/tbl0.pak` / `pack/tbl1.pak` `missing` counts and `validate_output.py` blank-field errors. If TBL offsets moved, run:

```powershell
python relocate_tbl_overrides.py --apply
python "E:\DBO Zero 2.0_tools\hanhua\build_output.py"
python validate_output.py
```

`relocate_tbl_overrides.py` backs up `tbl_overrides.tsv`, relocates rows whose source text has a unique new position, converts safe repeated UTF-16LE rows to `*` wildcard rows, and comments unresolved ambiguous rows instead of deleting them. After a source refresh, also regenerate reference-only lookup files from `src_file`:

```powershell
python install_hanhua.py --game-dir src_file export --out untranslated.tsv
python install_hanhua.py --game-dir src_file export-taiwan --out taiwan_translated.tsv
python install_hanhua.py export-tbl --source-dir src_file --out tbl_candidates.tsv
```

Keep override files strictly separated by target file type:

- `overrides.tsv` is only for Taiwan/RDF outputs: `local_data.dat`, `local_sync_data.dat`, `table_text_all_data.rdf`, and `table_quest_text_data.rdf`.
- `lang0_overrides.tsv` is only for `pack/lang0.pak`.
- `tbl_overrides.tsv` is only for `pack/tbl0.pak` and `pack/tbl1.pak`.
- Do not put `lang0.pak` rows in `overrides.tsv`, and do not put Taiwan/RDF rows in `lang0_overrides.tsv` or `tbl_overrides.tsv`.
- Candidate files such as `taiwan_candidates.tsv`, `lang0_candidates.tsv`, and `tbl_candidates.tsv` are reference-only. Do not move candidate rows into any override file unless the user explicitly selects them.

Do not write UTF-8 encoded Chinese text into generated game-facing `output/` files. Line-based Taiwan key/value files such as `local_data.dat` and `local_sync_data.dat` must be generated as GBK so single-line Chinese messages render correctly in game. `pack/lang0.pak` overrides must also remain GBK byte patches. RDF and TBL files keep their binary fixed-width encodings and must not be converted to UTF-8.
