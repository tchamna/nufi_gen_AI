from __future__ import annotations

import csv
import os
from pathlib import Path


APP_NAME = "Clafrica Plus Customizable"
SHORTCUTS_FILE_NAME = "custom_shortcuts.tsv"
REMOVAL_SENTINEL = "\0REMOVED_SHORTCUT\0"
DEFAULT_SHORTCUTS_TEMPLATE = """# Clafrica Plus Customizable shortcuts
# Format: shortcut<TAB>replacement
# Remove a shortcut with: !shortcut
# One shortcut per line. Lines starting with # are ignored.
# Custom shortcuts are added on top of the built-in list.
# If the same shortcut already exists, your custom value overrides it.
# Examples:
# mba\tmbe'
# af \tɑ
# !mbk
"""


class ShortcutFileError(ValueError):
    pass


def get_user_shortcuts_path(app_name: str = APP_NAME) -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / app_name / SHORTCUTS_FILE_NAME
    return Path.home() / "AppData" / "Roaming" / app_name / SHORTCUTS_FILE_NAME


def ensure_shortcuts_file(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(DEFAULT_SHORTCUTS_TEMPLATE, encoding="utf-8")
    return path


def _parse_shortcuts_line(line: str, source_name: str, line_number: int) -> tuple[str, str] | None:
    if not line.strip():
        return None
    if line.lstrip().startswith("#"):
        return None
    if line.startswith("!"):
        key = line[1:]
        if not key:
            raise ShortcutFileError(f"{source_name} line {line_number}: shortcut is empty")
        return key, REMOVAL_SENTINEL
    if "\t" not in line:
        raise ShortcutFileError(
            f"{source_name} line {line_number}: use TAB between shortcut and replacement"
        )
    key, value = line.split("\t", 1)
    if not key:
        raise ShortcutFileError(f"{source_name} line {line_number}: shortcut is empty")
    if not value:
        raise ShortcutFileError(f"{source_name} line {line_number}: replacement is empty")
    return key, value


def parse_shortcuts_text(text: str) -> dict[str, str]:
    mappings: dict[str, str] = {}
    errors: list[str] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        try:
            parsed = _parse_shortcuts_line(line, "line", line_number)
        except ShortcutFileError as exc:
            errors.append(str(exc))
            continue
        if parsed is None:
            continue
        key, value = parsed
        mappings[key] = value
    if errors:
        raise ShortcutFileError("\n".join(errors[:5]))
    return mappings


def render_shortcuts_text(mappings: dict[str, str]) -> str:
    if not mappings:
        return ""
    lines: list[str] = []
    for key, value in mappings.items():
        if value == REMOVAL_SENTINEL:
            lines.append(f"!{key}\n")
        else:
            lines.append(f"{key}\t{value}\n")
    return "".join(lines)


def _parse_shortcuts_pairs(rows: list[tuple[str, str]], source_name: str) -> dict[str, str]:
    mappings: dict[str, str] = {}
    errors: list[str] = []
    for line_number, (key, value) in enumerate(rows, start=1):
        if not key and not value:
            continue
        if key.lstrip().startswith("#"):
            continue
        if key.startswith("!"):
            removal_key = key[1:]
            if not removal_key:
                errors.append(f"{source_name} line {line_number}: shortcut is empty")
                continue
            mappings[removal_key] = REMOVAL_SENTINEL
            continue
        if not key:
            errors.append(f"{source_name} line {line_number}: shortcut is empty")
            continue
        if not value:
            errors.append(f"{source_name} line {line_number}: replacement is empty")
            continue
        mappings[key] = value
    if errors:
        raise ShortcutFileError("\n".join(errors[:5]))
    return mappings


def _is_header_row(key: str, value: str) -> bool:
    key_name = key.strip().lower()
    value_name = value.strip().lower()
    return key_name in {"shortcut", "key", "trigger"} and value_name in {
        "replacement",
        "value",
        "output",
        "text",
    }


def _load_delimited_shortcuts(path: Path, delimiter: str | None = None) -> dict[str, str]:
    text = path.read_text(encoding="utf-8-sig")
    sample = text[:2048]
    if delimiter is None:
        try:
            delimiter = csv.Sniffer().sniff(sample, delimiters=",;\t").delimiter
        except csv.Error:
            delimiter = ","
    rows: list[tuple[str, str]] = []
    for raw_row in csv.reader(text.splitlines(), delimiter=delimiter):
        if not raw_row:
            continue
        if len(raw_row) < 2:
            rows.append((raw_row[0], ""))
            continue
        rows.append((raw_row[0], raw_row[1]))
    if rows and _is_header_row(rows[0][0], rows[0][1]):
        rows = rows[1:]
    return _parse_shortcuts_pairs(rows, path.name)


def _load_text_shortcuts(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8-sig")
    try:
        return parse_shortcuts_text(text)
    except ShortcutFileError:
        pass

    rows: list[tuple[str, str]] = []
    separators = ("\t", "=>", "->", "=", ";", ",")
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line.startswith("!"):
            rows.append((line, ""))
            continue
        pair: tuple[str, str] | None = None
        for separator in separators:
            if separator in line:
                key, value = line.split(separator, 1)
                pair = (key, value)
                break
        if pair is None:
            rows.append((line, ""))
            continue
        rows.append(pair)
    if rows and _is_header_row(rows[0][0], rows[0][1]):
        rows = rows[1:]
    return _parse_shortcuts_pairs(rows, path.name)


def load_import_shortcuts(path: Path) -> dict[str, str]:
    suffix = path.suffix.lower()
    if suffix == ".tsv":
        return _load_delimited_shortcuts(path, delimiter="\t")
    if suffix == ".csv":
        return _load_delimited_shortcuts(path)
    if suffix == ".txt":
        return _load_text_shortcuts(path)
    raise ShortcutFileError(
        f"Unsupported file type: {path.suffix or '(no extension)'}. Use .csv, .tsv, or .txt"
    )


def load_shortcuts(path: Path) -> dict[str, str]:
    shortcut_path = ensure_shortcuts_file(path)
    return parse_shortcuts_text(shortcut_path.read_text(encoding="utf-8"))


def save_shortcuts_text(path: Path, text: str) -> dict[str, str]:
    mappings = parse_shortcuts_text(text)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")
    return mappings
