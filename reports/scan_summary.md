# hanhua v3 scan summary

This scan is read-only. It does not modify game files or generated output.

## Current catalog

- lang0: 5266
- taiwan: 238792
- tbl: 59517

## Current files

- lang0/lang0.pak: 5266
- taiwan/local_data.dat: 4021
- taiwan/local_sync_data.dat: 1205
- taiwan/table_quest_text_data.rdf: 151337
- taiwan/table_text_all_data.rdf: 82229
- tbl/tbl0.pak: 5641
- tbl/tbl1.pak: 53876

## Imported manual translations

- lang0: 928
- taiwan: 253
- tbl: 1880
- total: 3061

## Imported legacy candidates

- total: 151132

## Generated files

- data/translations.tsv: 3061 rows
- data/catalog_current.tsv: 303575 rows
- data/workbench.tsv: 62050 rows
- data/candidates_unified.tsv: 62050 rows
- reports/overlaps_by_text.tsv: 632 rows
- reports/overlaps_by_id.tsv: 5218 rows
- reports/translation_conflicts.tsv: 18 rows
- reports/review_conflicts.md: 16 rows
- reports/review_overlaps.md: 80 rows
- reports/what_to_do_next.md: 1 rows

## Policy notes

- Taiwan text is now reference material, not the primary translation source.
- Manual translations imported from legacy override TSV files are marked accepted.
- Candidate suggestions from old candidate TSV files are reference-only.
- Existing translations in data/translations.tsv are treated as the editable v3 master table.
- Use data/workbench.tsv as the simple queue for new translations or old translation changes.
- TBL entries are scanned from the current source snapshot and must be reconciled after every game update.
