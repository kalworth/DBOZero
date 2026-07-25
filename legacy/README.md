# Legacy Files

This directory keeps the pre-v3 toolchain and data for reference and migration.

- `tools/`: old build, install, patch, relocation, and validation scripts.
  The patching modules still used by v3 (`install_hanhua`, `lang0_gbk_patch`,
  `tbl_utf16_patch`, `console_color`, `auto_translate_new_source`) now live in
  `hanhua_v3/runtime/`; the files here are thin compatibility shims that
  re-export them so archived scripts keep working.
- `translations/`: old manual override TSV files.
- `candidates/`: old reference-only candidate and exported text TSV files.
- `reports/`: old cleanup, relocation, and audit reports.
- `docs/`: old notes.
- `assets/`: old screenshots and reference images.

The v3 tools read from this directory when importing historical translations.
Do not treat these files as the new active workflow.
