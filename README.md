# DBO Zero Hanhua Workspace

This workspace is moving to the v3 rewrite.

Root-level layout:

- `src_file/DBOZero/`: current game source snapshot.
- `hanhua_v3/`: new unified tooling.
- `data/`: v3 normalized translation data and generated discovery tables.
- `reports/`: v3 scan reports.
- `legacy/`: old scripts, old TSV files, old reports, and reference assets.
- `output/` and `output_taiwan/`: generated patch outputs, ignored by Git.
- `release/`: historical release packages, ignored by Git.

Run the current v3 discovery scan from this directory:

```powershell
python -m hanhua_v3.scan
```

The scan imports old manual translations from `legacy/translations/`, reads
old reference candidates from `legacy/candidates/`, and writes unified v3
tables/reports without modifying game files or generated output.

Important policy:

- Current game files in `src_file/DBOZero` are the source of truth.
- Taiwan text is reference material, not the primary translation source.
- `data/translations.tsv` is the v3 manual translation seed.
- `data/catalog_current.tsv` and `data/candidates_unified.tsv` are generated
  and can be recreated with `python -m hanhua_v3.scan`.
- `data/workbench.tsv` is generated for daily editing. Fill `zh_cn_new` when
  adding a new translation or changing an old one; do not edit the full catalog
  by hand.
