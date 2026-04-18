from __future__ import annotations

import csv
import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

import nufi_model as nm


BASE_DIR = Path(__file__).resolve().parent
AUDIO_MAPPING_CSV_PATH = (
    BASE_DIR / "android-keyboard" / "app" / "src" / "main" / "assets" / "nufi_word_list.csv"
)
_AUDIO_MAPPING_EXPORT = "export const audioMapping"
_PAIR_RE = re.compile(r'^\s*"((?:[^"\\]|\\.)*)"\s*:\s*"((?:[^"\\]|\\.)*)"\s*,?\s*$')


def _unescape_ts_string(value: str) -> str:
    return (
        value.replace(r"\\", "\\")
        .replace(r"\"", '"')
        .replace(r"\n", "\n")
        .replace(r"\r", "\r")
        .replace(r"\t", "\t")
    )


def normalize_audio_word(word: str) -> str:
    if not word:
        return ""
    return nm.normalize_text(word).lower().strip()


def _strip_low_tone_only(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text)
    stripped = decomposed.replace("\u0300", "")
    return unicodedata.normalize("NFC", stripped)


def _build_low_tone_key_index(mapping: dict[str, str]) -> dict[str, str]:
    index: dict[str, str] = {}
    for key, value in mapping.items():
        canonical = _strip_low_tone_only(key)
        previous = index.get(canonical)
        if previous is not None and previous != value:
            raise ValueError(
                f"Conflicting audio mappings for canonical key {canonical!r}: "
                f"{previous!r} vs {value!r}"
            )
        index[canonical] = value
    return index


def _load_audio_mapping_from_csv(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            key = normalize_audio_word((row.get("nufi_keyword") or "").strip())
            value = (row.get("audio_file") or "").strip()
            if key and value:
                mapping[key] = value

    if not mapping:
        raise ValueError(f"No audio mappings parsed from {path}")

    return mapping


def _load_audio_mapping_from_ts(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")

    export_index = text.find(_AUDIO_MAPPING_EXPORT)
    if export_index < 0:
        raise ValueError(f"Could not find {_AUDIO_MAPPING_EXPORT!r} in {path}")

    body_start = text.find("{", export_index)
    body_end = text.find("};", body_start)
    if body_start < 0 or body_end < 0:
        raise ValueError(f"Could not find audio mapping object body in {path}")

    body = text[body_start + 1 : body_end]
    mapping: dict[str, str] = {}

    for line in body.splitlines():
        match = _PAIR_RE.match(line)
        if not match:
            continue
        raw_key, raw_value = match.groups()
        key = normalize_audio_word(_unescape_ts_string(raw_key))
        value = _unescape_ts_string(raw_value).strip()
        if key and value:
            mapping[key] = value

    if not mapping:
        raise ValueError(f"No audio mappings parsed from {path}")

    return mapping


@lru_cache(maxsize=None)
def load_audio_mapping(mapping_path: str | Path = AUDIO_MAPPING_CSV_PATH) -> dict[str, str]:
    path = Path(mapping_path)
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return _load_audio_mapping_from_csv(path)
    if suffix == ".ts":
        return _load_audio_mapping_from_ts(path)

    raise ValueError(f"Unsupported audio mapping format for {path}")


@lru_cache(maxsize=1)
def _low_tone_audio_key_index() -> dict[str, str]:
    return _build_low_tone_key_index(load_audio_mapping())


def get_audio_filename(word: str, mapping: dict[str, str] | None = None) -> str | None:
    if not word:
        return None

    active_mapping = mapping if mapping is not None else load_audio_mapping()
    cleaned_word = normalize_audio_word(word)
    if not cleaned_word:
        return None

    exact = active_mapping.get(cleaned_word)
    if exact:
        return exact

    canonical = _strip_low_tone_only(cleaned_word)
    if mapping is not None:
        return _build_low_tone_key_index(active_mapping).get(canonical)
    return _low_tone_audio_key_index().get(canonical)


def build_s3_audio_url(
    audio_filename: str,
    bucket_name: str,
    region: str,
) -> str:
    key = quote(f"{audio_filename}.mp3", safe="/")
    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{key}"
