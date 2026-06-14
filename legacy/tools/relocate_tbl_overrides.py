# -*- coding: utf-8 -*-
"""
Relocate tbl_overrides.tsv after the source tbl0/tbl1 files are refreshed.

The script is conservative:
- exact rows that still match the current source are kept unchanged;
- exact rows whose source text appears once in the same pak are moved there;
- repeated exact rows with the same file/source/translation may become one
  wildcard row when that source text still exists;
- unresolved rows are commented out and reported instead of being deleted.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import shutil
from dataclasses import dataclass
from pathlib import Path

import tbl_utf16_patch as tbl


@dataclass(frozen=True)
class ParsedRow:
    line_index: int
    row_no: int
    cells: list[str]
    file_name: str
    offset: int | None
    source_text: str
    translation: str


def parse_offset(value: str) -> int | None:
    value = value.strip()
    if value in tbl.ALL_OFFSETS:
        return None
    return int(value, 16) if value.lower().startswith("0x") else int(value)


def read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8-sig").splitlines()


def parse_rows(lines: list[str]) -> list[ParsedRow]:
    rows: list[ParsedRow] = []
    for line_index, line in enumerate(lines):
        stripped = line.lstrip()
        if not stripped or stripped.startswith("#"):
            continue
        parsed = next(csv.reader([line], delimiter="\t"))
        row_no = line_index + 1
        if len(parsed) < 4 or parsed[0].lower() == "file" or parsed[0] not in tbl.TBL_FILES:
            continue
        source_text = parsed[2]
        translation = parsed[3]
        if not source_text or not translation:
            continue
        rows.append(
            ParsedRow(
                line_index=line_index,
                row_no=row_no,
                cells=parsed,
                file_name=parsed[0],
                offset=parse_offset(parsed[1]),
                source_text=source_text,
                translation=translation,
            )
        )
    return rows


def tsv_line(cells: list[str]) -> str:
    return "\t".join(cells)


def find_all(data: bytes, needle: bytes) -> list[int]:
    if not needle:
        return []
    return tbl.find_all(data, needle)


def row_mode_at(data: bytes, row: ParsedRow, offset: int) -> str | None:
    utf16_source = row.source_text.encode("utf-16le")
    if 0 <= offset and offset + len(utf16_source) <= len(data) and data[offset : offset + len(utf16_source)] == utf16_source:
        return "utf16"
    if row.source_text.isascii():
        ascii_source = row.source_text.encode("ascii")
        if 0 <= offset and offset + len(ascii_source) <= len(data) and data[offset : offset + len(ascii_source)] == ascii_source:
            return "ascii"
    return None


def replacement_fits(row: ParsedRow, mode: str, single_byte_encoding: str) -> bool:
    if mode == "utf16":
        return len(row.translation.encode("utf-16le")) <= len(row.source_text.encode("utf-16le"))
    if mode == "ascii":
        return len(row.translation.encode(single_byte_encoding)) <= len(row.source_text.encode("ascii"))
    return False


def candidate_hits(data: bytes, row: ParsedRow) -> list[tuple[int, str]]:
    hits: list[tuple[int, str]] = [(offset, "utf16") for offset in find_all(data, row.source_text.encode("utf-16le"))]
    if not hits and row.source_text.isascii():
        hits = [(offset, "ascii") for offset in find_all(data, row.source_text.encode("ascii"))]
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="Relocate tbl_overrides.tsv offsets for the current src_file snapshot.")
    parser.add_argument("--apply", action="store_true", help="Write tbl_overrides.tsv. Without this, only print a summary.")
    parser.add_argument("--overrides", type=Path, default=Path("tbl_overrides.tsv"))
    parser.add_argument("--source-dir", type=Path, default=Path("src_file"))
    parser.add_argument("--encoding", default="gbk", help="Single-byte encoding used for ASCII TBL fields. Default: gbk.")
    args = parser.parse_args()

    overrides_path = args.overrides.resolve()
    lines = read_lines(overrides_path)
    rows = parse_rows(lines)
    data = {file_name: tbl.tbl_path(args.source_dir.resolve(), file_name).read_bytes() for file_name in tbl.TBL_FILES}

    rows_by_line = {row.line_index: row for row in rows}
    active_groups: dict[tuple[str, str, str], list[ParsedRow]] = {}
    for row in rows:
        if row.offset is not None:
            active_groups.setdefault((row.file_name, row.source_text, row.translation), []).append(row)

    wildcard_groups: set[tuple[str, str, str]] = {
        (row.file_name, row.source_text, row.translation)
        for row in rows
        if row.offset is None and candidate_hits(data[row.file_name], row)
    }

    rewritten = list(lines)
    stats = {
        "kept_valid": 0,
        "kept_wildcard": 0,
        "relocated_unique": 0,
        "converted_wildcard": 0,
        "commented_duplicate": 0,
        "commented_missing": 0,
        "commented_ambiguous": 0,
        "commented_no_fit": 0,
    }
    report_rows: list[list[str]] = [["row_no", "action", "file", "old_id", "new_id", "source_text", "translation", "note"]]
    converted_groups: set[tuple[str, str, str]] = set()

    for row in rows:
        group_key = (row.file_name, row.source_text, row.translation)
        old_id = row.cells[1].strip()
        file_data = data[row.file_name]

        if row.offset is None:
            hits = candidate_hits(file_data, row)
            if hits:
                stats["kept_wildcard"] += 1
                report_rows.append([str(row.row_no), "kept_wildcard", row.file_name, old_id, old_id, row.source_text, row.translation, f"hits={len(hits)}"])
                continue
            rewritten[row.line_index] = "# DISABLED_MISSING_AFTER_SOURCE_REFRESH\t" + lines[row.line_index]
            stats["commented_missing"] += 1
            report_rows.append([str(row.row_no), "commented_missing", row.file_name, old_id, "", row.source_text, row.translation, "wildcard source text not found"])
            continue

        current_mode = row_mode_at(file_data, row, row.offset)
        if current_mode and replacement_fits(row, current_mode, args.encoding):
            stats["kept_valid"] += 1
            report_rows.append([str(row.row_no), "kept_valid", row.file_name, old_id, old_id, row.source_text, row.translation, current_mode])
            continue
        if current_mode:
            rewritten[row.line_index] = "# DISABLED_NO_FIT_AFTER_SOURCE_REFRESH\t" + lines[row.line_index]
            stats["commented_no_fit"] += 1
            report_rows.append([str(row.row_no), "commented_no_fit", row.file_name, old_id, old_id, row.source_text, row.translation, current_mode])
            continue

        hits = [(offset, mode) for offset, mode in candidate_hits(file_data, row) if replacement_fits(row, mode, args.encoding)]
        if len(hits) == 1:
            offset, mode = hits[0]
            cells = list(row.cells)
            cells[1] = f"0x{offset:08X}"
            rewritten[row.line_index] = tsv_line(cells)
            stats["relocated_unique"] += 1
            report_rows.append([str(row.row_no), "relocated_unique", row.file_name, old_id, cells[1], row.source_text, row.translation, mode])
            continue

        if len(hits) > 1:
            group_rows = active_groups.get(group_key, [])
            can_wildcard = all(mode == "utf16" for _offset, mode in hits)
            if can_wildcard and len(group_rows) > 1 and group_key not in converted_groups and group_key not in wildcard_groups:
                cells = list(row.cells)
                cells[1] = "*"
                rewritten[row.line_index] = tsv_line(cells)
                converted_groups.add(group_key)
                stats["converted_wildcard"] += 1
                report_rows.append([str(row.row_no), "converted_wildcard", row.file_name, old_id, "*", row.source_text, row.translation, f"hits={len(hits)}"])
                continue
            rewritten[row.line_index] = "# DISABLED_DUPLICATE_AFTER_SOURCE_REFRESH\t" + lines[row.line_index]
            stats["commented_duplicate" if group_key in converted_groups or group_key in wildcard_groups else "commented_ambiguous"] += 1
            report_rows.append([str(row.row_no), "commented_ambiguous", row.file_name, old_id, "", row.source_text, row.translation, f"hits={len(hits)}"])
            continue

        rewritten[row.line_index] = "# DISABLED_MISSING_AFTER_SOURCE_REFRESH\t" + lines[row.line_index]
        stats["commented_missing"] += 1
        report_rows.append([str(row.row_no), "commented_missing", row.file_name, old_id, "", row.source_text, row.translation, "source text not found"])

    print("TBL relocation summary:")
    for key, value in stats.items():
        print(f"{key}={value}")

    if args.apply:
        stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = overrides_path.with_name(f"{overrides_path.stem}.backup_before_source_refresh_{stamp}{overrides_path.suffix}")
        report = overrides_path.with_name(f"tbl_relocation_report_{stamp}.tsv")
        shutil.copy2(overrides_path, backup)
        overrides_path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")
        with report.open("w", encoding="utf-8-sig", newline="") as handle:
            csv.writer(handle, delimiter="\t").writerows(report_rows)
        print(f"Backed up: {backup}")
        print(f"Wrote: {overrides_path}")
        print(f"Report: {report}")
    else:
        print("Dry run only. Re-run with --apply to write changes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
