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

- Edit existing accepted translations in `data/translations.tsv`.
- Use generated `data/workbench.tsv` as the simple daily queue.
- In `data/workbench.tsv`, fill `zh_cn_new` only for rows you want to add or
  change.
- `data/catalog_current.tsv` and `data/candidates_unified.tsv` are generated
  discovery outputs; do not hand-edit them.
