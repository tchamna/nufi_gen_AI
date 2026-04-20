#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path
import sys
import unicodedata


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import nufi_model as nm


OUT_UNIQUE = ROOT / "data" / "nufi_unique_words.txt"
OUT_UNIQUE_ALPHA = ROOT / "data" / "nufi_unique_words_alpha.txt"
OUT_TOP_100 = ROOT / "data" / "nufi_top_100.txt"
OUT_TOP_100_NO_NUMERICS = ROOT / "data" / "nufi_top_100_no_numerics.txt"
OUT_TOP_100_PREVIEW = ROOT / "data" / "nufi_top_100_preview.txt"


def _has_unicode_letter(text: str) -> bool:
    return any(unicodedata.category(ch).startswith("L") for ch in text)


def _is_numeric_or_pointer_token(token: str) -> bool:
    allowed_non_digit = {" ", "-", ">", ".", ",", ":", ";", "/", "\\", "(", ")"}
    saw_digit = False
    for ch in token:
        if ch.isdigit():
            saw_digit = True
            continue
        if ch in allowed_non_digit:
            continue
        return False
    return saw_digit


def _is_alpha_word_token(token: str) -> bool:
    saw_letter = False
    for ch in token:
        cat = unicodedata.category(ch)
        if cat.startswith("L"):
            saw_letter = True
            continue
        if cat == "Mn":
            continue
        if ch in {"'", "’", "-", " "}:
            continue
        return False
    return saw_letter


def _iter_filtered_tokens() -> list[str]:
    bundle = nm.load_corpus_bundle(str(ROOT))
    tokens: list[str] = []
    for sentence in bundle["sentence_sources"]:
        if not sentence or not _has_unicode_letter(sentence):
            continue
        for token in sentence.split():
            if not token:
                continue
            if _is_numeric_or_pointer_token(token):
                continue
            if not _has_unicode_letter(token):
                continue
            tokens.append(token)
    return tokens


def _write_lines(path: Path, lines: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = "\n".join(lines)
    if content:
        content += "\n"
    path.write_text(content, encoding="utf-8-sig")


def _format_top(counter: Counter[str], limit: int) -> list[str]:
    ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return [f"{token}\t{count}" for token, count in ranked[:limit]]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    tokens = _iter_filtered_tokens()
    alpha_tokens = [token for token in tokens if _is_alpha_word_token(token)]

    unique_words = sorted(set(tokens))
    unique_alpha_words = sorted(set(alpha_tokens))
    counts = Counter(tokens)
    alpha_counts = Counter(alpha_tokens)

    _write_lines(OUT_UNIQUE, unique_words)
    _write_lines(OUT_UNIQUE_ALPHA, unique_alpha_words)
    _write_lines(OUT_TOP_100, _format_top(counts, 100))
    _write_lines(OUT_TOP_100_NO_NUMERICS, _format_top(alpha_counts, 100))
    _write_lines(OUT_TOP_100_PREVIEW, _format_top(alpha_counts, 30))

    print(f"Wrote {OUT_UNIQUE}")
    print(f"Wrote {OUT_UNIQUE_ALPHA}")
    print(f"Wrote {OUT_TOP_100}")
    print(f"Wrote {OUT_TOP_100_NO_NUMERICS}")
    print(f"Wrote {OUT_TOP_100_PREVIEW}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
