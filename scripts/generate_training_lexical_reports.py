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

# Mixed-source corpora still contain a small number of foreign names / metadata
# tokens that should not end up in the Nufi lexical reports.
LEXICAL_EXCLUDE_WORDS = frozenset(
    {
        "'non",
        "akonǒ",
        "amsconse",
        "anaclac",
        "anoblie",
        "aprí",
        "balafon",
        "bali",
        "bamakó",
        "bamileke",
        "bamilekes",
        "bamilekē",
        "bibiane",
        "blangī",
        "bouque",
        "ceintre",
        "chuengoue",
        "jeremie",
        "sadembouo",
        "tchamna",
        "yameni",
    }
)


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


def _sentence_lexical_text(sentence: str) -> str:
    if "=" not in sentence:
        return sentence

    _left, right = sentence.split("=", 1)
    return right.strip()


def _should_exclude_lexical_token(token: str) -> bool:
    return token in LEXICAL_EXCLUDE_WORDS


def _iter_filtered_tokens() -> list[str]:
    bundle = nm.load_corpus_bundle(str(ROOT))
    return _iter_filtered_tokens_from_sentence_sources(bundle["sentence_sources"])


def _iter_filtered_tokens_from_sentence_sources(sentence_sources: dict[str, list[dict]]) -> list[str]:
    tokens: list[str] = []
    for sentence in sentence_sources:
        if not sentence or not _has_unicode_letter(sentence):
            continue
        lexical_text = _sentence_lexical_text(sentence)
        if not lexical_text or not _has_unicode_letter(lexical_text):
            continue
        for token in lexical_text.split():
            if not token:
                continue
            if _is_numeric_or_pointer_token(token):
                continue
            if not _has_unicode_letter(token):
                continue
            if _should_exclude_lexical_token(token):
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


def build_lexical_report_data(
    sentence_sources: dict[str, list[dict]] | None = None,
    top_limit: int = 100,
    preview_limit: int = 30,
) -> dict[str, object]:
    if sentence_sources is None:
        bundle = nm.load_corpus_bundle(str(ROOT))
        sentence_sources = bundle["sentence_sources"]

    tokens = _iter_filtered_tokens_from_sentence_sources(sentence_sources)
    alpha_tokens = [token for token in tokens if _is_alpha_word_token(token)]
    unique_words = sorted(set(tokens))
    unique_alpha_words = sorted(set(alpha_tokens))
    counts = Counter(tokens)
    alpha_counts = Counter(alpha_tokens)

    return {
        "total_tokens": len(tokens),
        "total_alpha_tokens": len(alpha_tokens),
        "unique_words": unique_words,
        "unique_alpha_words": unique_alpha_words,
        "top_words": _format_top(counts, top_limit),
        "top_alpha_words": _format_top(alpha_counts, top_limit),
        "top_alpha_preview": _format_top(alpha_counts, preview_limit),
    }


def write_lexical_reports(report_data: dict[str, object]) -> None:
    unique_words = [str(item) for item in report_data["unique_words"]]
    unique_alpha_words = [str(item) for item in report_data["unique_alpha_words"]]
    top_words = [str(item) for item in report_data["top_words"]]
    top_alpha_words = [str(item) for item in report_data["top_alpha_words"]]
    top_alpha_preview = [str(item) for item in report_data["top_alpha_preview"]]

    _write_lines(OUT_UNIQUE, unique_words)
    _write_lines(OUT_UNIQUE_ALPHA, unique_alpha_words)
    _write_lines(OUT_TOP_100, top_words)
    _write_lines(OUT_TOP_100_NO_NUMERICS, top_alpha_words)
    _write_lines(OUT_TOP_100_PREVIEW, top_alpha_preview)


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    write_lexical_reports(build_lexical_report_data())

    print(f"Wrote {OUT_UNIQUE}")
    print(f"Wrote {OUT_UNIQUE_ALPHA}")
    print(f"Wrote {OUT_TOP_100}")
    print(f"Wrote {OUT_TOP_100_NO_NUMERICS}")
    print(f"Wrote {OUT_TOP_100_PREVIEW}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
