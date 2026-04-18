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


def _strip_diacritics(text: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def normalize_audio_word(word: str) -> str:
    if not word:
        return ""
    return nm.normalize_text(word).lower().strip()


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
def _normalized_audio_key_index() -> dict[str, tuple[tuple[str, str], ...]]:
    index: dict[str, list[tuple[str, str]]] = {}
    for key, value in load_audio_mapping().items():
        normalized_key = _strip_diacritics(key)
        index.setdefault(normalized_key, []).append((key, value))
    return {key: tuple(matches) for key, matches in index.items()}


def _assume_low_tone_word(word: str) -> str:
    tokens = []
    changed = False
    for token in word.split():
        if not token or nm._has_tone_or_diacritic(token):
            tokens.append(token)
            continue

        updated = token
        token_changed = False
        for i, ch in enumerate(updated):
            low_tone = nm._BARE_VOWEL_TO_LOW_TONE.get(ch)
            if not low_tone:
                continue
            updated = updated[:i] + low_tone + updated[i + 1 :]
            token_changed = True

        if token_changed:
            tokens.append(updated)
            changed = True
        else:
            tokens.append(token)
    if not changed:
        return word
    return " ".join(tokens)


def _is_unmarked_word(word: str) -> bool:
    tokens = word.split()
    return bool(tokens) and not any(nm._has_tone_or_diacritic(token) for token in tokens)


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

    if cleaned_word in {"bà", "ba\u0300"}:
        return "ba1"

    low_tone_word = _assume_low_tone_word(cleaned_word)
    if low_tone_word != cleaned_word:
        low_tone_exact = active_mapping.get(low_tone_word)
        if low_tone_exact:
            return low_tone_exact

    if _is_unmarked_word(cleaned_word):
        return None

    normalized_word = _strip_diacritics(cleaned_word)
    if mapping is not None:
        normalized_matches = tuple(
            (key, value)
            for key, value in active_mapping.items()
            if _strip_diacritics(key) == normalized_word
        )
    else:
        normalized_matches = _normalized_audio_key_index().get(normalized_word, ())

    if len(normalized_matches) == 1:
        return normalized_matches[0][1]

    if low_tone_word != cleaned_word:
        for key, value in normalized_matches:
            if key == low_tone_word:
                return value

    return None


def build_s3_audio_url(
    audio_filename: str,
    bucket_name: str,
    region: str,
) -> str:
    key = quote(f"{audio_filename}.mp3", safe="/")
    return f"https://{bucket_name}.s3.{region}.amazonaws.com/{key}"
