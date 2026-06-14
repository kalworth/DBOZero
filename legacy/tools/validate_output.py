# -*- coding: utf-8 -*-
"""
Validate generated DBOZ Chinese patch output folders.

This script is read-only. It checks that the generated output folders contain
the expected files, use the intended ANSI encodings, preserve pack file sizes,
and do not reintroduce tbl1.pak length-prefixed NUL display risks.
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from pathlib import Path

import console_color
import install_hanhua
import lang0_gbk_patch


LOCALIZATION_FILES = (
    "local_data.dat",
    "local_sync_data.dat",
    "table_text_all_data.rdf",
    "table_quest_text_data.rdf",
)
PACK_FILES = ("lang0.pak", "tbl0.pak", "tbl1.pak")
TBL_FILES = ("tbl0.pak", "tbl1.pak")
ALL_OFFSETS = {"", "*", "all", "ALL"}


@dataclass(frozen=True)
class TblRow:
    row_no: int
    file_name: str
    offset: int | None
    source_text: str
    translation: str


class ValidationError(RuntimeError):
    pass


def tool_dir() -> Path:
    return Path(__file__).resolve().parent


def dbo_root(base: Path) -> Path:
    return base / "DBOZero"


def language_dir(base: Path) -> Path:
    return dbo_root(base) / "localize" / "Taiwan" / "language"


def pack_dir(base: Path) -> Path:
    return dbo_root(base) / "pack"


def require_file(path: Path, errors: list[str]) -> None:
    if not path.is_file():
        errors.append(f"Missing file: {path}")


def validate_required_files(base: Path, label: str, errors: list[str]) -> None:
    for name in LOCALIZATION_FILES:
        require_file(language_dir(base) / name, errors)
    for name in PACK_FILES:
        require_file(pack_dir(base) / name, errors)
    if not errors:
        print(console_color.ok(f"OK {label} required files"))


def validate_decoding(path: Path, encoding: str, errors: list[str]) -> None:
    try:
        path.read_bytes().decode(encoding)
    except UnicodeDecodeError as exc:
        errors.append(f"Cannot decode {path} as {encoding}: {exc}")
        return
    print(console_color.ok(f"OK decode {path} as {encoding}"))


def validate_output_encodings(base: Path, label: str, encoding: str, errors: list[str]) -> None:
    validate_decoding(language_dir(base) / "local_data.dat", encoding, errors)
    validate_decoding(language_dir(base) / "local_sync_data.dat", encoding, errors)
    print(console_color.ok(f"OK {label} ANSI encoding checks"))


def validate_tbl_sizes(source_dir: Path, base: Path, label: str, errors: list[str]) -> None:
    for name in TBL_FILES:
        source = pack_dir(source_dir) / name
        output = pack_dir(base) / name
        if not source.is_file() or not output.is_file():
            continue
        if source.stat().st_size != output.stat().st_size:
            errors.append(
                f"TBL size changed for {label}/{name}: "
                f"{source.stat().st_size} -> {output.stat().st_size}"
            )
            continue
        print(console_color.ok(f"OK {label} {name} size={output.stat().st_size}"))


def validate_lang0_size(source_dir: Path, base: Path, label: str, errors: list[str]) -> None:
    source = pack_dir(source_dir) / "lang0.pak"
    output = pack_dir(base) / "lang0.pak"
    if not source.is_file() or not output.is_file():
        return
    if source.stat().st_size != output.stat().st_size:
        errors.append(
            f"lang0.pak size changed for {label}: "
            f"{source.stat().st_size} -> {output.stat().st_size}"
        )
        return
    print(console_color.ok(f"OK {label} lang0.pak size={output.stat().st_size}"))


def find_lang0_output_value(data: bytes, key: str) -> bytes | None:
    start = lang0_gbk_patch.find_lang0_value_start(data, key)
    if start < 0:
        return None
    end = lang0_gbk_patch.find_lang0_value_end(data, start, key)
    return lang0_gbk_patch.unescape_lang0_value(data[start:end])


def validate_lang0_values(
    base: Path,
    label: str,
    encoding: str,
    rows: list[tuple[str, str]],
    text_transform,
    errors: list[str],
) -> None:
    output = pack_dir(base) / "lang0.pak"
    if not output.is_file():
        return
    data = output.read_bytes()
    expected_rows = list({key: text_transform(text) for key, text in rows}.items())
    checked = 0
    bad = 0
    for key, expected in expected_rows:
        raw = find_lang0_output_value(data, key)
        if raw is None:
            continue
        checked += 1
        try:
            actual = raw.decode(encoding)
        except UnicodeDecodeError as exc:
            bad += 1
            if bad <= 20:
                errors.append(f"{label} lang0 {key} cannot decode as {encoding}: {exc}")
            continue
        if actual != expected:
            bad += 1
            if bad <= 20:
                errors.append(f"{label} lang0 {key} mismatch: {actual!r} != {expected!r}")
    if bad == 0:
        print(console_color.ok(f"OK {label} lang0 values checked={checked}, bad=0"))


def parse_offset(value: str, row_no: int, errors: list[str]) -> int | None:
    value = value.strip()
    if value in ALL_OFFSETS:
        return None
    try:
        return int(value, 16) if value.lower().startswith("0x") else int(value)
    except ValueError:
        errors.append(f"Invalid tbl_overrides.tsv offset at row {row_no}: {value}")
        return None


def read_tbl_rows(path: Path, errors: list[str]) -> list[TblRow]:
    rows: list[TblRow] = []
    if not path.is_file():
        errors.append(f"Missing tbl overrides file: {path}")
        return rows
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row_no, row in enumerate(reader, 1):
            if not row or not row[0].strip() or row[0].lstrip().startswith("#"):
                continue
            if len(row) < 4:
                errors.append(f"Invalid tbl_overrides.tsv row {row_no}; need file, id, source_text, translation")
                continue
            file_name = row[0].strip()
            if file_name.lower() == "file":
                continue
            if file_name not in TBL_FILES:
                errors.append(f"Unsupported tbl file at row {row_no}: {file_name}")
                continue
            source_text = row[2]
            translation = row[3]
            if not source_text or not translation:
                continue
            rows.append(TblRow(row_no, file_name, parse_offset(row[1], row_no, errors), source_text, translation))
    return rows


def validate_tbl1_length_prefixes(
    source_dir: Path,
    base: Path,
    label: str,
    rows: list[TblRow],
    errors: list[str],
) -> None:
    source_path = pack_dir(source_dir) / "tbl1.pak"
    output_path = pack_dir(base) / "tbl1.pak"
    if not source_path.is_file() or not output_path.is_file():
        return
    source_data = source_path.read_bytes()
    output_data = output_path.read_bytes()
    checked = 0
    bad = 0

    for row in rows:
        if row.file_name != "tbl1.pak" or row.offset is None:
            continue
        offset = row.offset
        source_bytes = row.source_text.encode("utf-16le")
        if offset < 2 or offset + len(source_bytes) > len(source_data):
            continue
        if source_data[offset : offset + len(source_bytes)] != source_bytes:
            continue
        source_units = len(source_bytes) // 2
        if int.from_bytes(source_data[offset - 2 : offset], "little") != source_units:
            continue

        checked += 1
        output_units = int.from_bytes(output_data[offset - 2 : offset], "little")
        if output_units != source_units:
            bad += 1
            if bad <= 20:
                errors.append(
                    f"{label} tbl1 row {row.row_no} offset 0x{offset:08X} changed length prefix "
                    f"{source_units} -> {output_units}: {row.source_text!r}"
                )
            continue
        text_bytes = output_data[offset : offset + output_units * 2]
        text = text_bytes.decode("utf-16le", errors="replace")
        if "\x00" in text:
            bad += 1
            if bad <= 20:
                errors.append(
                    f"{label} tbl1 row {row.row_no} offset 0x{offset:08X} reads NUL "
                    f"with length {output_units}: {row.source_text!r}"
                )

    if bad == 0:
        print(console_color.ok(f"OK {label} tbl1 length prefixes checked={checked}, bad=0"))


def validate_tbl0_not_blank(base: Path, label: str, rows: list[TblRow], errors: list[str]) -> None:
    output_path = pack_dir(base) / "tbl0.pak"
    if not output_path.is_file():
        return
    output_data = output_path.read_bytes()
    checked = 0
    bad = 0
    for row in rows:
        if row.file_name != "tbl0.pak" or row.offset is None:
            continue
        source_len = len(row.source_text.encode("utf-16le"))
        if row.offset < 0 or row.offset + source_len > len(output_data):
            continue
        field = output_data[row.offset : row.offset + source_len]
        checked += 1
        if not field.strip(b"\x00"):
            bad += 1
            if bad <= 20:
                errors.append(f"{label} tbl0 row {row.row_no} offset 0x{row.offset:08X} patched field is blank")
    if bad == 0:
        print(console_color.ok(f"OK {label} tbl0 blank-field check checked={checked}, bad=0"))


def validate_variant(
    source_dir: Path,
    base: Path,
    label: str,
    encoding: str,
    rows: list[TblRow],
    lang0_rows: list[tuple[str, str]],
    text_transform,
    errors: list[str],
) -> None:
    validate_required_files(base, label, errors)
    validate_output_encodings(base, label, encoding, errors)
    validate_lang0_size(source_dir, base, label, errors)
    validate_lang0_values(base, label, encoding, lang0_rows, text_transform, errors)
    validate_tbl_sizes(source_dir, base, label, errors)
    validate_tbl1_length_prefixes(source_dir, base, label, rows, errors)
    validate_tbl0_not_blank(base, label, rows, errors)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    root = tool_dir()
    source_dir = root / "src_file"
    errors: list[str] = []
    rows = read_tbl_rows(root / "tbl_overrides.tsv", errors)
    try:
        lang0_rows = lang0_gbk_patch.read_overrides(root / "lang0_overrides.tsv")
    except lang0_gbk_patch.PatchError as exc:
        errors.append(str(exc))
        lang0_rows = []

    validate_variant(source_dir, root / "output", "output", "gbk", rows, lang0_rows, install_hanhua.to_simplified, errors)
    validate_variant(source_dir, root / "output_taiwan", "output_taiwan", "cp950", rows, lang0_rows, install_hanhua.to_traditional, errors)

    if errors:
        print(console_color.error("Validation failed:"))
        for error in errors:
            print(console_color.error(f"- {error}"))
        return 2
    print(console_color.ok("Validation passed."))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
