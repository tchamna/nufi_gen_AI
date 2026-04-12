# -*- coding: utf-8 -*-
"""
Classify Nufi lemmas as Bana vs non-Bana using the same Bana dictionary keys as
`nufi_bana_standard_maps.py` (excludes `dict_ton_bas`).

Shared by `dump_bana_headword_audit.py` and `build_local_dictionary_db.py`.
"""

from __future__ import annotations

import unicodedata

try:
    from .nufi_bana_standard_maps import (
        dict_bana_to_standard,
        dict_bana_to_standard_ab_am,
        dict_bana_to_standard_one_chr,
        dict_bana_to_standard_three_chr,
        dict_bana_to_standard_two_chr,
        dict_ton_bas,
        vowel_bana_to_komako,
    )
except ImportError:
    from nufi_bana_standard_maps import (
        dict_bana_to_standard,
        dict_bana_to_standard_ab_am,
        dict_bana_to_standard_one_chr,
        dict_bana_to_standard_three_chr,
        dict_bana_to_standard_two_chr,
        dict_ton_bas,
        vowel_bana_to_komako,
    )


def collect_bana_keys() -> list[str]:
    keys: set[str] = set()
    for d in (
        dict_bana_to_standard,
        dict_bana_to_standard_one_chr,
        dict_bana_to_standard_two_chr,
        dict_bana_to_standard_three_chr,
        dict_bana_to_standard_ab_am,
        vowel_bana_to_komako,
    ):
        keys.update(d.keys())
    return sorted(keys, key=len, reverse=True)


def first_matching_bana_key(word: str, sorted_keys: list[str]) -> str | None:
    nfc = unicodedata.normalize("NFC", word.strip())
    for key in sorted_keys:
        if not key:
            continue
        k = unicodedata.normalize("NFC", key)
        if k in nfc:
            return key
    return None


def orthography_category_for_lemma(word: str, sorted_keys: list[str] | None = None) -> str:
    keys = sorted_keys if sorted_keys is not None else collect_bana_keys()
    return "bana" if first_matching_bana_key(word, keys) is not None else "non_bana"


def _collect_bana_replacement_pairs() -> list[tuple[str, str]]:
    """Same map set as `collect_bana_keys` (excludes `dict_ton_bas`). Longest keys first."""
    pairs: list[tuple[str, str]] = []
    for d in (
        dict_bana_to_standard_three_chr,
        dict_bana_to_standard_two_chr,
        dict_bana_to_standard_ab_am,
        dict_bana_to_standard_one_chr,
        dict_bana_to_standard,
        vowel_bana_to_komako,
    ):
        pairs.extend(d.items())
    pairs.sort(key=lambda kv: len(kv[0]), reverse=True)
    return pairs


_REPLACEMENT_PAIRS: list[tuple[str, str]] | None = None


def _cached_bana_replacement_pairs() -> list[tuple[str, str]]:
    global _REPLACEMENT_PAIRS
    if _REPLACEMENT_PAIRS is None:
        _REPLACEMENT_PAIRS = _collect_bana_replacement_pairs()
    return _REPLACEMENT_PAIRS


def normalize_bana_to_standard(text: str) -> str:
    """Rewrite Bana substrings to Komako using `nufi_bana_standard_maps` (longest match first)."""
    if not text:
        return text
    out = text
    for key, value in _cached_bana_replacement_pairs():
        if key:
            out = out.replace(key, value)
    return out


def _collect_ton_bas_pairs() -> list[tuple[str, str]]:
    pairs = list(dict_ton_bas.items())
    pairs.sort(key=lambda kv: len(kv[0]), reverse=True)
    return pairs


_TON_BAS_PAIRS: list[tuple[str, str]] | None = None


def _cached_ton_bas_pairs() -> list[tuple[str, str]]:
    global _TON_BAS_PAIRS
    if _TON_BAS_PAIRS is None:
        _TON_BAS_PAIRS = _collect_ton_bas_pairs()
    return _TON_BAS_PAIRS


def normalize_ton_bas(text: str) -> str:
    """Strip low tone to base letters using `dict_ton_bas` (after Bana→Komako)."""
    if not text:
        return text
    out = text
    for key, value in _cached_ton_bas_pairs():
        if key:
            out = out.replace(key, value)
    return out


__all__ = [
    "collect_bana_keys",
    "first_matching_bana_key",
    "normalize_bana_to_standard",
    "normalize_ton_bas",
    "orthography_category_for_lemma",
]
