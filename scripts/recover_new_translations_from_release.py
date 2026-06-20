from __future__ import annotations

import argparse
import csv
import re
import shutil
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hanhua_v3 import scan  # noqa: E402


RELEASE_ROOT = ROOT / "release" / "\u7b80\u4e2dv2.6.5" / "DBOZero"
QUEUE_PATH = ROOT / "data" / "new_translations.tsv"
TBL_FILES = {"tbl0.pak", "tbl1.pak"}
CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]")

COL_FILE = "\u6587\u4ef6"
COL_POSITION = "\u4f4d\u7f6e"
COL_SOURCE_TEXT = "\u539f\u6587"
COL_TRANSLATION = "\u586b\u5199\u4e2d\u6587"


def has_cjk(text: str) -> bool:
    return bool(CJK_RE.search(text or ""))


def git_blob(path: Path) -> bytes:
    safe_dir = ROOT.as_posix()
    return subprocess.check_output(
        ["git", "-c", f"safe.directory={safe_dir}", "show", f"HEAD:{path.as_posix()}"],
        cwd=ROOT,
    )


def decode_lang_text(data: bytes) -> str:
    for encoding in ("gbk", "utf-8-sig", "utf-8", "cp950"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            pass
    return data.decode("gbk", errors="replace")


def parse_lang(data: bytes) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in decode_lang_text(data).splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not re.fullmatch(r"[A-Za-z0-9_]+", key or ""):
            continue
        if value.startswith('"'):
            value = value[1:]
            if value.endswith('"'):
                value = value[:-1]
            value = value.replace('""', '"')
        out[key] = value
    return out


def clean_text(text: str) -> str:
    return (text or "").strip("\x00").strip()


def decode_single_byte_slice(data: bytes) -> str:
    for encoding in ("gbk", "cp950", "utf-8"):
        try:
            return clean_text(data.decode(encoding))
        except UnicodeDecodeError:
            pass
    return clean_text(data.decode("gbk", errors="ignore"))


def resolve_text_map(values_by_source: dict[str, list[str]]) -> tuple[dict[str, str], int, int]:
    resolved: dict[str, str] = {}
    conflicts = 0
    value_count = 0
    for source_text, values in values_by_source.items():
        value_count += len(values)
        counts = Counter(values)
        ranked = counts.most_common()
        if len(ranked) == 1 or ranked[0][1] > ranked[1][1]:
            resolved[source_text] = ranked[0][0]
        else:
            conflicts += 1
    return resolved, conflicts, value_count


def build_lang_release_maps(release_root: Path) -> tuple[dict[str, str], dict[str, str], dict[str, int]]:
    old_lang = parse_lang(git_blob(Path("src_file/DBOZero/pack/lang0.pak")))
    release_lang = parse_lang((release_root / "pack" / "lang0.pak").read_bytes())

    by_key: dict[str, str] = {}
    by_source_values: dict[str, list[str]] = defaultdict(list)
    for key, old_text in old_lang.items():
        release_text = release_lang.get(key, "")
        if old_text and release_text and old_text != release_text and has_cjk(release_text):
            by_key[key] = release_text
            by_source_values[old_text].append(release_text)

    by_source, conflicts, value_count = resolve_text_map(by_source_values)
    return by_key, by_source, {
        "lang0_key_changed": len(by_key),
        "lang0_source_resolved": len(by_source),
        "lang0_source_conflicts": conflicts,
        "lang0_values": value_count,
    }


def iter_tbl_candidates(data: bytes):
    for match in re.finditer(rb"[ -~]{4,}", data):
        text, char_shift = scan.normalize_tbl_candidate_text(match.group().decode("ascii", errors="replace"))
        if not scan.tbl_accepted_candidate_text(text) or scan.is_noise_text(text):
            continue
        yield text, match.start() + char_shift, "single"

    for offset, raw_text in scan.iter_utf16le_printable_runs(data):
        text, char_shift = scan.normalize_tbl_candidate_text(raw_text, strip_length_prefix=True)
        if not scan.tbl_accepted_candidate_text(text) or scan.is_noise_text(text):
            continue
        yield text, offset + char_shift * 2, "utf16le"


def build_tbl_release_map(release_root: Path) -> tuple[dict[str, str], dict[str, int]]:
    by_source_values: dict[str, list[str]] = defaultdict(list)
    scanned = 0
    changed = 0

    for file_name in sorted(TBL_FILES):
        old = git_blob(Path(f"src_file/DBOZero/pack/{file_name}"))
        release = (release_root / "pack" / file_name).read_bytes()

        for source_text, offset, encoding in iter_tbl_candidates(old):
            scanned += 1
            if encoding == "utf16le":
                byte_len = len(source_text.encode("utf-16le"))
                release_text = clean_text(
                    release[offset : offset + byte_len].decode("utf-16le", errors="ignore")
                )
            else:
                byte_len = len(source_text.encode("ascii", errors="ignore"))
                release_text = decode_single_byte_slice(release[offset : offset + byte_len])

            if release_text and release_text != source_text and has_cjk(release_text):
                changed += 1
                by_source_values[source_text].append(release_text)

    by_source, conflicts, value_count = resolve_text_map(by_source_values)
    return by_source, {
        "tbl_candidates_scanned": scanned,
        "tbl_changed_hits": changed,
        "tbl_source_resolved": len(by_source),
        "tbl_source_conflicts": conflicts,
        "tbl_values": value_count,
    }


def read_accepted_text_map(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    out: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        for row in reader:
            status = (row.get("status") or "").strip().casefold()
            if status not in {"", "accepted", "active", "ok", "keep"}:
                continue
            source_text = row.get("source_text") or ""
            translation = row.get("zh_cn") or ""
            if source_text and translation and has_cjk(translation):
                out.setdefault(source_text, translation)
    return out


def tbl_translation_fits(source_text: str, translation: str) -> bool:
    try:
        return len(translation.encode("utf-16le")) <= len(source_text.encode("utf-16le"))
    except UnicodeEncodeError:
        return False


def fill_queue(
    queue_path: Path,
    accepted_by_source: dict[str, str],
    lang_by_key: dict[str, str],
    lang_by_source: dict[str, str],
    tbl_by_source: dict[str, str],
    dry_run: bool,
) -> dict[str, int | str]:
    with queue_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    changed = 0
    skipped_too_long = 0
    already_filled = 0

    for row in rows:
        current = row.get(COL_TRANSLATION) or ""
        if current.strip():
            already_filled += 1
            continue

        file_name = (row.get(COL_FILE) or "").strip()
        item_id = (row.get(COL_POSITION) or "").strip()
        source_text = row.get(COL_SOURCE_TEXT) or ""
        translation = accepted_by_source.get(source_text, "")

        if not translation and file_name == "lang0.pak":
            translation = lang_by_key.get(item_id, "") or lang_by_source.get(source_text, "")
        elif not translation and file_name in TBL_FILES:
            translation = tbl_by_source.get(source_text, "")

        if not translation or not has_cjk(translation):
            continue
        if file_name in TBL_FILES and not tbl_translation_fits(source_text, translation):
            skipped_too_long += 1
            continue

        row[COL_TRANSLATION] = translation
        changed += 1

    backup_path = ""
    if changed and not dry_run:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = queue_path.with_name(f"{queue_path.stem}.backup_before_release_recover_{stamp}{queue_path.suffix}")
        shutil.copy2(queue_path, backup)
        backup_path = str(backup)
        with queue_path.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, delimiter="\t", fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    total_filled = sum(1 for row in rows if (row.get(COL_TRANSLATION) or "").strip())
    return {
        "queue_rows": len(rows),
        "already_filled": already_filled,
        "filled_blank_rows": changed,
        "skipped_too_long": skipped_too_long,
        "total_filled_after": total_filled,
        "backup": backup_path,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Recover new_translations.tsv from the saved simplified release.")
    parser.add_argument("--release-root", type=Path, default=RELEASE_ROOT)
    parser.add_argument("--queue", type=Path, default=QUEUE_PATH)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    args = parse_args(argv)
    release_root = args.release_root.resolve()
    queue_path = args.queue.resolve()

    if not release_root.is_dir():
        raise SystemExit(f"Missing release root: {release_root}")
    if not queue_path.is_file():
        raise SystemExit(f"Missing queue file: {queue_path}")

    lang_by_key, lang_by_source, lang_stats = build_lang_release_maps(release_root)
    tbl_by_source, tbl_stats = build_tbl_release_map(release_root)
    accepted_by_source = read_accepted_text_map(ROOT / "data" / "translations.tsv")
    fill_stats = fill_queue(
        queue_path,
        accepted_by_source,
        lang_by_key,
        lang_by_source,
        tbl_by_source,
        args.dry_run,
    )

    print(f"release_root={release_root}")
    print(f"dry_run={args.dry_run}")
    print(f"accepted_text_map={len(accepted_by_source)}")
    for stats in (lang_stats, tbl_stats, fill_stats):
        for key, value in stats.items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
