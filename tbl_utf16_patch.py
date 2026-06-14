# -*- coding: utf-8 -*-
"""
DBO Zero tbl0/tbl1 fixed-field patcher.

This patcher preserves file size and all unrelated bytes. UTF-16LE replacements
must fit inside the original UTF-16LE string field. Exact-offset ASCII fields are
also supported with GBK replacements. Unused bytes are padded with NUL characters
so later binary offsets do not move and UI text does not gain visible trailing
spaces.
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path


TBL_FILES = ("tbl0.pak", "tbl1.pak")
ALL_OFFSETS = {"", "*", "all", "ALL"}


class PatchError(RuntimeError):
    pass


@dataclass(frozen=True)
class TblOverride:
    file_name: str
    offset: int | None
    source_text: str
    translation: str


def tool_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def default_source_dir() -> Path:
    return tool_dir() / "src_file"


def dbo_root(source_dir: Path) -> Path:
    return source_dir / "DBOZero"


def tbl_path(source_dir: Path, file_name: str) -> Path:
    return dbo_root(source_dir) / "pack" / file_name


def parse_offset(value: str, row_no: int) -> int | None:
    value = value.strip()
    if value in ALL_OFFSETS:
        return None
    try:
        return int(value, 16) if value.lower().startswith("0x") else int(value)
    except ValueError as exc:
        raise PatchError(f"Invalid tbl_overrides.tsv offset at row {row_no}: {value}") from exc


def read_overrides(path: Path | None) -> list[TblOverride]:
    if path is None:
        path = tool_dir() / "tbl_overrides.tsv"
    if not path.exists():
        raise PatchError(f"Missing tbl overrides file: {path}")

    rows: list[TblOverride] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, delimiter="\t")
        for row_no, row in enumerate(reader, 1):
            if not row or not row[0].strip() or row[0].lstrip().startswith("#"):
                continue
            if len(row) < 4:
                raise PatchError(f"Invalid tbl_overrides.tsv row {row_no}; need file, id, source_text, translation")
            file_name = row[0].strip()
            if file_name.lower() == "file":
                continue
            if file_name not in TBL_FILES:
                raise PatchError(f"Unsupported tbl file at row {row_no}: {file_name}")
            source_text = row[2]
            translation = row[3]
            if not source_text or not translation:
                continue
            rows.append(TblOverride(file_name, parse_offset(row[1], row_no), source_text, translation))
    return rows


def utf16le(text: str, label: str) -> bytes:
    try:
        return text.encode("utf-16le")
    except UnicodeEncodeError as exc:
        raise PatchError(f"{label} cannot be encoded as UTF-16LE: {text}") from exc


def encoded_text_bytes(text: str, label: str, encoding: str) -> bytes:
    try:
        return text.encode(encoding)
    except UnicodeEncodeError as exc:
        raise PatchError(f"{label} cannot be encoded as {encoding}: {text}") from exc


def fixed_replacement(source_text: str, translation: str, pad_unit: bytes = b"\x00\x00") -> bytes:
    source = utf16le(source_text, "Source text")
    replacement = utf16le(translation, "Translation")
    if len(replacement) > len(source):
        raise PatchError(
            f"Translation is too long for fixed tbl field: {source_text!r} -> {translation!r} "
            f"({len(replacement)} bytes > {len(source)} bytes)"
        )
    pad_bytes = len(source) - len(replacement)
    if pad_bytes % 2:
        raise PatchError(f"Unexpected odd UTF-16LE byte length for source text: {source_text!r}")
    return replacement + (pad_unit * (pad_bytes // 2))


def fixed_single_byte_replacement(source: bytes, source_text: str, translation: str, encoding: str = "gbk") -> bytes:
    replacement = encoded_text_bytes(translation, "Translation", encoding)
    if len(replacement) > len(source):
        raise PatchError(
            f"Translation is too long for fixed single-byte tbl field: {source_text!r} -> {translation!r} "
            f"({len(replacement)} bytes > {len(source)} bytes)"
        )
    return replacement + (b"\x00" * (len(source) - len(replacement)))


def has_length_prefix(
    data: bytes | bytearray,
    file_name: str,
    offset: int,
    source_units: int,
) -> bool:
    if file_name != "tbl1.pak" or offset < 2:
        return False
    length_pos = offset - 2
    return int.from_bytes(data[length_pos:offset], "little") == source_units


def find_all(data: bytes, needle: bytes) -> list[int]:
    offsets: list[int] = []
    start = 0
    while True:
        idx = data.find(needle, start)
        if idx < 0:
            return offsets
        offsets.append(idx)
        start = idx + len(needle)


def patch_tbl_bytes(data: bytes, rows: list[TblOverride], single_byte_encoding: str = "gbk") -> tuple[bytes, dict[str, int]]:
    original = bytes(data)
    patched = bytearray(data)
    changed = 0
    missing = 0
    space_padded = 0

    ordered_rows = [
        row
        for _index, row in sorted(
            enumerate(rows),
            key=lambda item: (
                -len(utf16le(item[1].source_text, "Source text")),
                item[1].offset is None,
                item[0],
            ),
        )
    ]

    for row in ordered_rows:
        source = utf16le(row.source_text, "Source text")
        source_units = len(source) // 2
        pad_unit = b"\x20\x00" if has_length_prefix(patched, row.file_name, row.offset or -1, source_units) else b"\x00\x00"
        replacement = fixed_replacement(row.source_text, row.translation, pad_unit)
        if row.offset is not None:
            offset = row.offset
            if 0 <= offset and offset + len(source) <= len(patched) and bytes(patched[offset : offset + len(source)]) == source:
                patched[offset : offset + len(source)] = replacement
                if pad_unit == b"\x20\x00":
                    space_padded += 1
                changed += 1
                continue

            # Some tbl candidates are single-byte display names. Only patch
            # these by exact offset so wildcard rows do not rewrite identifiers.
            if row.source_text.isascii():
                single_source = row.source_text.encode("ascii")
                if (
                    0 <= offset
                    and offset + len(single_source) <= len(patched)
                    and bytes(patched[offset : offset + len(single_source)]) == single_source
                ):
                    patched[offset : offset + len(single_source)] = fixed_single_byte_replacement(
                        single_source, row.source_text, row.translation, single_byte_encoding
                    )
                    changed += 1
                    continue
            missing += 1
            continue

        offsets = find_all(bytes(patched), source)
        if not offsets:
            if find_all(original, source):
                continue
            missing += 1
            continue
        for offset in offsets:
            if offset is None or offset < 0 or offset + len(source) > len(patched):
                missing += 1
                continue
            if bytes(patched[offset : offset + len(source)]) != source:
                missing += 1
                continue
            patched[offset : offset + len(source)] = replacement
            if pad_unit == b"\x20\x00":
                space_padded += 1
            changed += 1
    return bytes(patched), {"rows": len(rows), "changed": changed, "missing": missing, "space_padded": space_padded}


def patch_tbl_pack(
    source_dir: Path,
    out_pack_dir: Path,
    rows: list[TblOverride],
    single_byte_encoding: str = "gbk",
) -> dict[str, dict[str, int]]:
    grouped: dict[str, list[TblOverride]] = {name: [] for name in TBL_FILES}
    for row in rows:
        grouped[row.file_name].append(row)

    out_pack_dir.mkdir(parents=True, exist_ok=True)
    stats: dict[str, dict[str, int]] = {}
    for file_name in TBL_FILES:
        file_rows = grouped[file_name]
        if not file_rows:
            continue
        source = tbl_path(source_dir, file_name)
        if not source.is_file():
            raise PatchError(f"Missing source tbl file: {source}")
        patched, file_stats = patch_tbl_bytes(source.read_bytes(), file_rows, single_byte_encoding)
        (out_pack_dir / file_name).write_bytes(patched)
        stats[file_name] = file_stats
    return stats


def command_plan(args: argparse.Namespace) -> int:
    source_dir = args.source_dir.resolve()
    rows = read_overrides(args.overrides)
    stats: dict[str, dict[str, int]] = {}
    for file_name in TBL_FILES:
        file_rows = [row for row in rows if row.file_name == file_name]
        if not file_rows:
            continue
        source = tbl_path(source_dir, file_name)
        if not source.is_file():
            raise PatchError(f"Missing source tbl file: {source}")
        _patched, stats[file_name] = patch_tbl_bytes(source.read_bytes(), file_rows)

    print(f"Source dir: {source_dir}")
    print("No files were changed by plan mode.")
    for file_name, values in stats.items():
        print(f"{file_name}: rows={values['rows']}, would_change={values['changed']}, missing={values['missing']}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="DBO Zero tbl0/tbl1 UTF-16LE fixed-field patcher")
    parser.add_argument("--source-dir", type=Path, default=default_source_dir())
    parser.add_argument("--overrides", type=Path, default=tool_dir() / "tbl_overrides.tsv")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan")
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "plan":
            return command_plan(args)
    except PatchError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
