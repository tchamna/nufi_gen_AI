from __future__ import annotations

import re
import unicodedata
from functools import lru_cache
from pathlib import Path
from urllib.parse import quote

import nufi_model as nm


BASE_DIR = Path(__file__).resolve().parent
AUDIO_MAPPING_PATH = BASE_DIR / "audioMapping.ts"
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


@lru_cache(maxsize=1)
def load_audio_mapping(mapping_path: str | Path = AUDIO_MAPPING_PATH) -> dict[str, str]:
    path = Path(mapping_path)
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
        low_tone = nm._first_bare_vowel_to_low_tone_word(token)
        if low_tone is not None and low_tone != token:
            tokens.append(low_tone)
            changed = True
        else:
            tokens.append(token)
    if not changed:
        return word
    return " ".join(tokens)


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
