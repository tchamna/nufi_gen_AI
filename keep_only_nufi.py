#!/usr/bin/env python3
"""keep_only_nufi.py

Usage: cat infile.txt | python keep_only_nufi.py > outfile.txt

This script tokenizes input text, marks obvious French/English tokens using
stopword lists, and keeps only tokens that are not identified as French/English.
Punctuation is preserved only when attached to kept tokens.
"""
from __future__ import annotations

import sys
import re
import unicodedata
import csv
from pathlib import Path
from zipfile import ZipFile


NUIFI_LEXICON: set[str] = set()
NUFI_DISTINCTIVE_CHARS = set("ɑəʉɔŋǒǎěǐǔɔ̀ɔ́ɑ̀ɑ́ə̀ə́ʉ̀ʉ́")


# Common French stopwords (not exhaustive) and common function words
FRENCH_STOPWORDS = {
    "le", "la", "les", "un", "une", "des", "de", "du", "au", "aux",
    "et", "ou", "où", "mais", "donc", "or", "ni", "car", "parceque", "parce", "que",
    "qui", "quoi", "dont", "sur", "sous", "avec", "sans", "pour", "dans", "entre",
    "à", "a", "aujourd'hui", "elle", "il", "ils", "elles", "on", "nous", "vous", "tu",
    "son", "sa", "ses", "leur", "leurs", "mon", "ma", "mes", "ton", "ta", "tes",
    "ce", "cet", "cette", "ces", "être", "avoir", "faire", "aller", "venir", "commencer",
    "commença", "appelé", "appelait", "appelé", "appel", "par", "si", "non", "oui",
    "dans", "sur", "sous", "avec", "sans", "chez", "dont", "comme", "ainsi", "très",
}

# Common English stopwords (small subset)
ENGLISH_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "there", "their", "they",
    "we", "you", "i", "he", "she", "it", "of", "in", "on", "for", "to", "is", "are",
    "was", "were", "be", "been", "have", "has", "had", "do", "does", "did",
}

WORD_RE = re.compile(r".+", re.UNICODE)


def _is_mark(char: str) -> bool:
    return unicodedata.category(char).startswith("M")


def _is_word_char(char: str) -> bool:
    category = unicodedata.category(char)
    return category[0] in {"L", "N"} or _is_mark(char) or char in {"'", "’"}


def _is_punct_char(char: str) -> bool:
    return unicodedata.category(char)[0] in {"P", "S"} and char not in {"'", "’"}


def normalize_token(tok: str) -> str:
    t = unicodedata.normalize("NFC", tok)
    return t.lower()


def load_nufi_lexicon() -> set[str]:
    lexicon: set[str] = set()
    try:
        lexicon_path = Path(__file__).with_name('nufi_word_list.csv')
        with lexicon_path.open(encoding='utf-8') as csvf:
            rdr = csv.reader(csvf)
            next(rdr, None)
            for row in rdr:
                if len(row) >= 3:
                    kw = normalize_token(row[2])
                    if kw:
                        lexicon.add(kw)
    except Exception:
        return set()
    return lexicon


def is_french_or_english_word(tok: str) -> bool:
    n = normalize_token(tok)
    if not n:
        return False
    # strip surrounding double-quotes and guillemets, but preserve apostrophes
    n = n.strip('"\u00ab\u00bb')
    if not n:
        return False
    # If token exists in the Nufi lexicon, treat as Nufi (not French/English)
    if n in NUIFI_LEXICON:
        return False

    # membership in stopword lists
    if n in FRENCH_STOPWORDS or n in ENGLISH_STOPWORDS:
        return True
    # heuristics: short ASCII-only words are likely French/English (e.g., 'le','la')
    if all(ord(c) < 128 for c in n) and len(n) <= 2:
        return True
    return False


def looks_like_nufi_word(tok: str) -> bool:
    # keep trailing/leading apostrophes (glottal-stop) intact for Nufi checks
    n = normalize_token(tok).strip('"\u00ab\u00bb')
    if not n:
        return False
    if n in NUIFI_LEXICON:
        return True
    if any(char in NUFI_DISTINCTIVE_CHARS for char in n):
        return True
    return False
    # keep trailing/leading apostrophes (glottal-stop) intact for Nufi checks


def tokenize(text: str) -> list[str]:
    # Preserve Unicode letters with combining marks by splitting only around
    # surrounding punctuation and whitespace, not inside grapheme-like words.
    tokens: list[str] = []
    for chunk in re.findall(r"\S+", text, flags=re.UNICODE):
        start = 0
        end = len(chunk)

        while start < end and _is_punct_char(chunk[start]):
            tokens.append(chunk[start])
            start += 1

        while end > start and _is_punct_char(chunk[end - 1]):
            end -= 1

        if start < end:
            tokens.append(chunk[start:end])

        for char in chunk[end:]:
            tokens.append(char)

    return tokens


def is_word_token(tok: str) -> bool:
    return bool(tok) and any(_is_word_char(char) for char in tok) and all(
        _is_word_char(char) for char in tok
    )


def score_text_side(text: str) -> dict[str, int]:
    tokens = tokenize(text)
    word_tokens = [tok for tok in tokens if is_word_token(tok)]
    nufi_count = sum(1 for tok in word_tokens if looks_like_nufi_word(tok))
    foreign_count = sum(1 for tok in word_tokens if is_french_or_english_word(tok))
    return {
        "word_count": len(word_tokens),
        "nufi_count": nufi_count,
        "foreign_count": foreign_count,
    }


def is_nufi_dominant(stats: dict[str, int]) -> bool:
    return stats["nufi_count"] > 0 and stats["nufi_count"] >= stats["foreign_count"]


def is_foreign_dominant(stats: dict[str, int]) -> bool:
    return stats["foreign_count"] > 0 and stats["foreign_count"] > stats["nufi_count"]


def resolve_colon_line(line: str) -> str | None:
    separator = re.search(r"\s:\s", line)
    if separator is None:
        return None

    left = line[:separator.start()].strip()
    right = line[separator.end():].strip()
    left = left.strip()
    right = right.strip()
    if not left or not right:
        return None

    left_stats = score_text_side(left)
    right_stats = score_text_side(right)

    left_nufi = is_nufi_dominant(left_stats)
    right_nufi = is_nufi_dominant(right_stats)

    if left_nufi and not right_nufi:
        return left
    if right_nufi and not left_nufi:
        return right
    if left_nufi and right_nufi:
        return line.strip()
    return None


def keep_only_nufi_line(line: str) -> str:
    colon_resolved = resolve_colon_line(line.strip())
    if colon_resolved is not None:
        return colon_resolved

    tokens = tokenize(line)
    keep = [False] * len(tokens)

    # mark word tokens
    for i, tok in enumerate(tokens):
        if is_word_token(tok):
            if looks_like_nufi_word(tok):
                keep[i] = True
        else:
            # punctuation -> defer decision
            keep[i] = False

    # attach punctuation to adjacent kept tokens
    for i, tok in enumerate(tokens):
        if not keep[i] and tok and all(_is_punct_char(char) for char in tok):
            left = i - 1
            right = i + 1
            if tok == ":":
                if left >= 0 and right < len(tokens) and keep[left] and keep[right]:
                    keep[i] = True
            elif left >= 0 and keep[left]:
                keep[i] = True
            elif right < len(tokens) and keep[right]:
                keep[i] = True

    out_tokens = [t for t, k in zip(tokens, keep) if k]
    if not out_tokens:
        return ""

    # join with spaces then remove space before punctuation
    s = " ".join(out_tokens)
    s = re.sub(r"\s+([,.;:!?])", r"\1", s)
    return s.strip()


def process_stream(instream, outstream):
    for line in instream:
        line = line.rstrip("\n")
        cleaned = keep_only_nufi_line(line)
        outstream.write(cleaned + "\n")


NUIFI_LEXICON = load_nufi_lexicon()


if __name__ == "__main__":
    def extract_text_from_docx(path: str) -> list[str]:
        try:
            texts = []
            with ZipFile(path) as z:
                with z.open('word/document.xml') as doc:
                    data = doc.read().decode('utf-8', errors='ignore')
                    parts = re.findall(r'<w:t[^>]*>(.*?)</w:t>', data, flags=re.DOTALL)
                    cur = []
                    for t in parts:
                        t2 = re.sub(r'<[^>]+>', '', t)
                        if t2.strip() == '':
                            if cur:
                                texts.append(' '.join(cur))
                                cur = []
                        else:
                            cur.append(t2)
                    if cur:
                        texts.append(' '.join(cur))
            return texts
        except Exception:
            return []

    if len(sys.argv) > 1:
        src = sys.argv[1]
        outpath = None
        outstream = sys.stdout
        if len(sys.argv) > 2:
            outpath = sys.argv[2]
            outstream = open(outpath, 'w', encoding='utf-8-sig', errors='ignore')

        try:
            if src.lower().endswith('.docx'):
                lines = extract_text_from_docx(src)
                for l in lines:
                    outstream.write(keep_only_nufi_line(l) + '\n')
            else:
                with open(src, encoding='utf-8', errors='ignore') as f:
                    process_stream(f, outstream)
        finally:
            if outpath and outstream is not sys.stdout:
                outstream.close()
    else:
        process_stream(sys.stdin, sys.stdout)
