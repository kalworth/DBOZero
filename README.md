# DBO Zero Hanhua Workspace

This workspace is moving to the v3 rewrite.

Daily translation workflow:

- Fill new translations in `data/待翻译_新增内容.tsv`.
- Change old translations in `data/translations.tsv`.
- Read `reports/what_to_do_next.md` if unsure.

Run the scan from this directory:

```powershell
python -m hanhua_v3.scan
```

The scan does not modify game files or generated output.
