# hanhua v3

This directory is the rewrite track for the DBO Zero localization toolchain.

The first milestone is a read-only discovery layer:

- scan the current `src_file/DBOZero` snapshot;
- import old manual translation TSV files as legacy data;
- build one unified catalog;
- build one unified candidate table;
- report overlaps between Taiwan, lang0, and tbl text.

The old toolchain stays available during the rewrite. New v3 commands should be
run from the repository root.

```powershell
python -m hanhua_v3.scan
```

Editing workflow:

- Main queue: `data/new_translations.tsv`.
- Fill only the `填写中文` column for new translations.
- Edit existing accepted translations in `data/translations.tsv` only when you
  intentionally want to change old text.
- `reports/internal/` and ignored generated TSV files are tool diagnostics, not
  the normal workflow.
