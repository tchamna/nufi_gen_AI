import math
import os
import pickle
import random
import re
import unicodedata

from nufi_bana_classification import normalize_bana_to_standard, normalize_ton_bas
from nufi_bana_standard_maps import dict_ton_bas

DEFAULT_ORDER = 4

# Inverse of dict_ton_bas for vowel bases only: bare vowel → low-tone form (lookup when user omits accents).
_VOWEL_BASES = frozenset(
    "aeiouAEIOU"
    "\u0251\u0254\u0259\u025b\u0289"  # ɑ ɔ ə ɛ ʉ
    "\u0186\u0190\u018f"  # Ɔ Ɛ Ə
)


def _build_bare_vowel_to_low_tone() -> dict[str, str]:
    out: dict[str, str] = {}
    for k, v in dict_ton_bas.items():
        if k == v:
            continue
        low = unicodedata.normalize("NFC", k)
        base = unicodedata.normalize("NFC", v)
        if len(base) != 1 or base not in _VOWEL_BASES:
            continue
        if base not in out:
            out[base] = low
    return out


_BARE_VOWEL_TO_LOW_TONE = _build_bare_vowel_to_low_tone()


def _has_tone_or_diacritic(s: str) -> bool:
    for ch in s:
        if unicodedata.category(ch) == "Mn":
            return True
        name = unicodedata.name(ch, "")
        if any(
            x in name
            for x in (
                "WITH GRAVE",
                "WITH ACUTE",
                "WITH CIRCUMFLEX",
                "WITH CARON",
                "WITH MACRON",
                "WITH DOUBLE GRAVE",
                "WITH DOT BELOW",
                "WITH TILDE",
                "WITH MIDDLE TILDE",
            )
        ):
            return True
    return False


def _first_bare_vowel_to_low_tone_word(word: str) -> str | None:
    """If the word has no tone marks, map the first bare vowel to low tone (ton bas)."""
    if not word or _has_tone_or_diacritic(word):
        return None
    w = unicodedata.normalize("NFC", word)
    for i, ch in enumerate(w):
        if ch in _BARE_VOWEL_TO_LOW_TONE:
            low = _BARE_VOWEL_TO_LOW_TONE[ch]
            return unicodedata.normalize("NFC", w[:i] + low + w[i + 1 :])
    return None


def _word_nufi_display_priority(word: str) -> int:
    """Higher = prefer when breaking equal-probability ties (Nufi letters over bare ASCII)."""
    if not word:
        return 0
    n = 0
    for ch in word:
        if ord(ch) > 127:
            n += 1
        elif unicodedata.category(ch) == "Mn":
            n += 1
    return n


def _tokens_assume_low_tone_bare_vowels(tokens: list[str]) -> tuple[list[str], bool]:
    out: list[str] = []
    changed = False
    for t in tokens:
        nxt = _first_bare_vowel_to_low_tone_word(t)
        if nxt is not None:
            out.append(nxt)
            changed = True
        else:
            out.append(t)
    return out, changed


DEFAULT_MAX_TOKENS = 40
DEFAULT_NUM_CANDIDATES = 5
DEFAULT_TEMPERATURE = 1.0
EXTERNAL_NUFI_ONLY_DIR = r"G:\My Drive\Data_Science\DataSets\Nufi\Nufi_Documents\Nufi_Only"

# Dictionary / gloss lines in vocabulary sources (French meta text, not Nufi).
_FRENCH_META_SUBSTRINGS = (
    "français",
    "francais",
    "expression française",
    "expression francaise",
    "correspond en français",
    "correspond en francais",
    "correspond en français",
    "traduit en français",
    "traduit en francais",
    "ce qui correspond",
    "cela correspond",
    "expression correspondant",
    "il se traduit",
    "l'expression correspondante",
    "l'expression française",
    "terme utilisé pour",
    "terme utilise pour",
    "en français camerounais",
    "déplorer la situation",
    "deplorer la situation",
)


def _text_has_french_meta(s: str) -> bool:
    t = s.lower()
    return any(sub in t for sub in _FRENCH_META_SUBSTRINGS)


def _exclude_sentence_for_nufi_only(raw: str, cleaned: str) -> bool:
    """Return True to drop a sentence (French dictionary gloss lines).

    Uses substring checks only — do not call langdetect here: it runs per line and
    makes startup unusably slow on large corpora (100k+ lines).
    """
    if _text_has_french_meta(raw) or _text_has_french_meta(cleaned):
        return True
    return False


# Latin "nota bene": after clean_text, "n. b." becomes two tokens "n" and "b", which
# trains a spurious n→b bigram. "n.b." collapses to one token "nb" and does not do that.
_RE_NOTA_BENE = re.compile(r"\bn\.\s*b\.", re.IGNORECASE)


def _strip_nota_bene_markers(text: str) -> str:
    """Remove N.B. / N. B. markers from raw lines before clean_text (corpus only)."""
    if not text:
        return text
    return _RE_NOTA_BENE.sub("", text)


def simple_ngrams(sentence, n, pad_left=True, pad_right=True):
    pad = [None] * (n - 1)
    items = list(sentence)
    if pad_left:
        items = pad + items
    if pad_right:
        items = items + pad
    for i in range(len(items) - n + 1):
        yield tuple(items[i:i + n])


def repair_mojibake(text):
    if not text:
        return text

    suspicious = ("\u00c3", "\u00c2", "\u00e2", "\u00cc", "\u00c9", "\u00f0")
    if not any(ch in text for ch in suspicious):
        return text

    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def normalize_text(text):
    if text is None:
        return ""

    text = repair_mojibake(text)
    text = text.replace("\ufeff", "")
    # Unify apostrophe-like characters so Bana maps (keys use ASCII ') match corpus tokens.
    text = (
        text.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u0060", "'")
        .replace("\u00b4", "'")
        .replace("\u02bc", "'")  # modifier letter apostrophe (common next to ə in orthography)
    )
    return unicodedata.normalize("NFC", text)


def clean_text(text, punct=None, apply_ton_bas=True):
    text = normalize_text(text)
    text = normalize_bana_to_standard(text)
    if apply_ton_bas:
        text = normalize_ton_bas(text)
    text = text.lower()
    if punct is None:
        punct = [".", ",", ";", ":", "!", "?"]
    for mark in punct:
        text = text.replace(mark, "")
    text = text.strip()
    return " ".join(text.split())


def _make_source_record(text, source_path, source_type, reference):
    return {
        "text": text,
        "source_path": source_path,
        "source_type": source_type,
        "reference": reference,
    }


def _read_records_from_text_file(path, source_type="txt", encoding="utf-8"):
    records = []
    with open(path, encoding=encoding, errors="ignore") as f:
        for line_number, line in enumerate(f.readlines(), start=1):
            if line.strip():
                records.append(_make_source_record(line, path, source_type, f"line {line_number}"))
    return records


def _read_records_from_docx(path):
    try:
        from docx import Document
    except Exception:
        return []

    records = []
    document = Document(path)
    for paragraph_number, paragraph in enumerate(document.paragraphs, start=1):
        if paragraph.text.strip():
            records.append(_make_source_record(paragraph.text, path, "docx", f"paragraph {paragraph_number}"))
    return records


def _read_records_from_srt(path):
    records = []
    raw_text = ""
    with open(path, encoding="utf-8-sig", errors="ignore") as f:
        raw_text = f.read()

    blocks = re.split(r"\r?\n\r?\n+", raw_text)
    timestamp_pattern = re.compile(r"^\d{2}:\d{2}:\d{2}[,.:]\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}[,.:]\d{3}$")
    subtitle_number = 0

    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        if lines[0].isdigit():
            lines = lines[1:]
        if lines and timestamp_pattern.match(lines[0]):
            lines = lines[1:]
        if not lines:
            continue

        subtitle_number += 1
        text = " ".join(lines)
        records.append(_make_source_record(text, path, "srt", f"subtitle {subtitle_number}"))

    return records


def _read_records_from_supported_file(path):
    lower_path = path.lower()
    if lower_path.endswith(".txt"):
        return _read_records_from_text_file(path, source_type="txt", encoding="utf-8-sig")
    if lower_path.endswith(".docx"):
        return _read_records_from_docx(path)
    if lower_path.endswith(".srt"):
        return _read_records_from_srt(path)
    return []


def _load_directory_records(folder_path):
    if not os.path.isdir(folder_path):
        return []

    records = []
    for root, _, file_names in os.walk(folder_path):
        for file_name in file_names:
            path = os.path.join(root, file_name)
            records.extend(_read_records_from_supported_file(path))
    return records


def _append_source(sentence_sources, cleaned_text, record):
    source_entry = {
        "path": record["source_path"],
        "type": record["source_type"],
        "reference": record["reference"],
    }
    sources = sentence_sources.setdefault(cleaned_text, [])
    key = (source_entry["path"], source_entry["reference"], source_entry["type"])
    if key not in {
        (existing["path"], existing["reference"], existing["type"])
        for existing in sources
    }:
        sources.append(source_entry)


def load_corpus_bundle(base_dir=None):
    if base_dir is None:
        base_dir = os.getcwd()

    records = []

    text_sources = [
        os.path.join(base_dir, "corpus_vocabulaire_nufi_test.txt"),
        os.path.join(base_dir, "main_file.txt"),
    ]
    for path in text_sources:
        if os.path.exists(path):
            records.extend(_read_records_from_text_file(path, source_type="txt", encoding="utf-8"))

    data_dir = os.path.join(base_dir, "data", "Nufi")
    if os.path.isdir(data_dir):
        for name in ("phrasebooknufi.txt", "conversation_base_nufi.txt"):
            path = os.path.join(data_dir, name)
            if os.path.exists(path):
                records.extend(_read_records_from_text_file(path, source_type="txt", encoding="utf-8"))

    local_nufi_docs_dir = os.path.join(base_dir, "data", "Nufi_Documents", "Nufi_Only")
    records.extend(_load_directory_records(local_nufi_docs_dir))
    records.extend(_load_directory_records(EXTERNAL_NUFI_ONLY_DIR))

    sentence_sources = {}
    cleaned_sentences = []
    seen = set()

    for record in records:
        cleaned = clean_text(_strip_nota_bene_markers(record["text"]))
        if not cleaned:
            continue
        if _exclude_sentence_for_nufi_only(record["text"], cleaned):
            continue
        _append_source(sentence_sources, cleaned, record)
        if cleaned not in seen:
            seen.add(cleaned)
            cleaned_sentences.append(cleaned)

    tokens = [sentence.split() for sentence in cleaned_sentences]
    return {
        "cleaned": cleaned_sentences,
        "tokens": tokens,
        "sentence_sources": sentence_sources,
    }


def load_corpus(base_dir=None):
    bundle = load_corpus_bundle(base_dir)
    return bundle["cleaned"], bundle["tokens"]


def build_ngram_model(nufi_tokens, n=DEFAULT_ORDER):
    model = {}
    for sentence in nufi_tokens:
        for gram in simple_ngrams(sentence, n):
            context = tuple(gram[:-1])
            next_word = gram[-1]
            model.setdefault(context, {})
            model[context][next_word] = model[context].get(next_word, 0) + 1

    for context, next_words in list(model.items()):
        total = float(sum(next_words.values())) if next_words else 1.0
        for word, count in list(next_words.items()):
            next_words[word] = count / total

    return model


def build_combined_model(nufi_tokens, max_n=5):
    combined = {}
    for n in range(2, max_n + 1):
        for sentence in nufi_tokens:
            pad = [None] * (n - 1)
            padded = pad + sentence + pad
            for i in range(len(padded) - n + 1):
                gram = padded[i:i + n]
                context = tuple(gram[:-1])
                next_word = gram[-1]
                combined.setdefault(context, {})
                combined[context][next_word] = combined[context].get(next_word, 0) + 1

    for context, next_words in list(combined.items()):
        total = float(sum(next_words.values())) if next_words else 1.0
        for word in list(next_words.keys()):
            next_words[word] = next_words[word] / total

    return combined


def save_model(model, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        pickle.dump(model, f)


def load_model(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def _available_context_length(model):
    try:
        key_lengths = {len(key) for key in model.keys() if isinstance(key, tuple)}
    except Exception:
        key_lengths = set()
    return max(key_lengths) if key_lengths else 1


def _requested_context_length(model, n):
    available = _available_context_length(model)
    requested = max(1, int(n) - 1)
    return min(available, requested)


def _find_choices_with_length(model, tokens_out, max_ctx):
    for k in range(min(len(tokens_out), max_ctx), 0, -1):
        key = tuple(tokens_out[-k:])
        if key in model and model[key]:
            return model[key], k

    if tuple() in model and model[tuple()]:
        return model[tuple()], 0

    return None, None


def _find_choices(model, tokens_out, max_ctx):
    choices, _ = _find_choices_with_length(model, tokens_out, max_ctx)
    return choices


def _weights_for_backoff_levels(n_levels: int, sparse_longest: bool) -> list[float]:
    """Weights for blending longest→shortest n-gram contexts (sum to 1).

    When the longest context has few distinct continuations, up-weight shorter
    contexts so unigram signal (e.g. after ``zǎ`` generally) is not drowned out.
    """
    if n_levels <= 0:
        return []
    if n_levels == 1:
        return [1.0]
    if n_levels == 2:
        return [0.55, 0.45] if sparse_longest else [0.62, 0.38]
    if n_levels == 3:
        if sparse_longest:
            return [0.12, 0.28, 0.60]
        return [0.45, 0.35, 0.20]
    raw = [0.5**i for i in range(n_levels)]
    s = sum(raw)
    return [w / s for w in raw]


def _interpolate_ngram_choices(model, tokens_out, max_ctx):
    """Blend next-word distributions from longest available context down to 1-gram.

    Using only the longest match hides plausible continuations when that context is
    sparse (few attested next words) while shorter contexts still carry signal
    (e.g. after ``zǎ`` generally, vs. a rare full ``kɑ' zhī zǎ`` trigram).
    """
    levels = []
    for k in range(min(len(tokens_out), max_ctx), 0, -1):
        key = tuple(tokens_out[-k:])
        ch = model.get(key)
        if not ch:
            continue
        if not any(w is not None for w in ch):
            continue
        levels.append((k, ch))
    if not levels:
        return None, None

    longest_ch = levels[0][1]
    n_distinct = sum(1 for w in longest_ch if w is not None)
    sparse_longest = n_distinct <= 4
    weights = _weights_for_backoff_levels(len(levels), sparse_longest)
    merged = {}
    for (k, ch), alpha in zip(levels, weights):
        for word, p in ch.items():
            if word is None:
                continue
            merged[word] = merged.get(word, 0) + alpha * float(p)

    primary_k = levels[0][0]
    return merged, primary_k


def _sample_word(choices, temperature):
    if temperature <= 0:
        return max(choices.items(), key=lambda item: item[1])[0]

    if math.isclose(temperature, 1.0):
        weighted = list(choices.items())
    else:
        weighted = []
        for word, probability in choices.items():
            adjusted = probability ** (1.0 / temperature)
            weighted.append((word, adjusted))

    total = sum(weight for _, weight in weighted)
    if total <= 0:
        return max(choices.items(), key=lambda item: item[1])[0]

    threshold = random.random() * total
    accumulator = 0.0
    for word, weight in weighted:
        accumulator += weight
        if accumulator >= threshold:
            return word

    return weighted[-1][0]


def _token_count(tokens_out):
    return sum(1 for token in tokens_out if token)


def generate_text_details(
    model,
    text,
    n=DEFAULT_ORDER,
    known_sentences=None,
    max_tokens=DEFAULT_MAX_TOKENS,
    temperature=DEFAULT_TEMPERATURE,
):
    normalized_text = clean_text(text)
    tokens = normalized_text.split()
    text_out = tokens[:]
    context_length = _requested_context_length(model, n)
    max_tokens = max(1, int(max_tokens))

    if not _find_choices(model, text_out, context_length):
        return {
            "status": "not_in_corpus",
            "normalized_text": normalized_text,
            "result": f"{' '.join(text_out)} not in corpus",
        }

    while _token_count(text_out) < max_tokens:
        choices = _find_choices(model, text_out, context_length)
        if not choices:
            break

        picked = _sample_word(choices, float(temperature))
        if picked is None:
            break

        text_out.append(picked)

        if context_length >= 2 and text_out[-(context_length - 1):] == [None] * (context_length - 1):
            break

    result = " ".join(token for token in text_out if token)
    status = "generated"
    if known_sentences is not None and result in known_sentences:
        status = "original"

    return {
        "status": status,
        "normalized_text": normalized_text,
        "result": result,
    }


def generate_candidates(
    model,
    text,
    n=DEFAULT_ORDER,
    known_sentences=None,
    max_tokens=DEFAULT_MAX_TOKENS,
    temperature=DEFAULT_TEMPERATURE,
    num_candidates=DEFAULT_NUM_CANDIDATES,
):
    normalized_text = clean_text(text)
    num_candidates = max(1, int(num_candidates))

    first = generate_text_details(
        model,
        normalized_text,
        n=n,
        known_sentences=known_sentences,
        max_tokens=max_tokens,
        temperature=temperature,
    )
    if first["status"] == "not_in_corpus":
        return normalized_text, [first]

    candidates = []
    seen = set()
    attempts = max(num_candidates * 6, 10)

    for _ in range(attempts):
        item = generate_text_details(
            model,
            normalized_text,
            n=n,
            known_sentences=known_sentences,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        key = item["result"]
        if key in seen:
            continue
        seen.add(key)
        candidates.append(item)
        if len(candidates) >= num_candidates:
            break

    if not candidates:
        candidates.append(first)

    return normalized_text, candidates


def find_corpus_matches(cleaned_sentences, query, limit=8):
    query = clean_text(query)
    limit = max(0, int(limit))
    if not query or limit == 0:
        return []

    exact = []
    contains = []
    for sentence in cleaned_sentences:
        if sentence == query:
            exact.append(sentence)
        elif query in sentence:
            contains.append(sentence)

    return (exact + contains)[:limit]


def find_corpus_matches_with_sources(sentence_sources, query, limit=8, max_sources=3):
    query = clean_text(query)
    limit = max(0, int(limit))
    max_sources = max(1, int(max_sources))
    if not query or limit == 0:
        return []

    exact = []
    contains = []
    for sentence, sources in sentence_sources.items():
        entry = {
            "text": sentence,
            "source_count": len(sources),
            "sources": sources[:max_sources],
        }
        if sentence == query:
            exact.append(entry)
        elif query in sentence:
            contains.append(entry)

    return (exact + contains)[:limit]


def suggest_next_words(model, text, n=DEFAULT_ORDER, limit=5):
    normalized_text = clean_text(text)
    tokens = normalized_text.split()
    context_length = _requested_context_length(model, n)
    choices, used_context = _interpolate_ngram_choices(model, tokens, context_length)

    # Older pickles may still index contexts under tone-marked tokens (e.g. "pèn") while
    # clean_text maps "pèn" → "pen". Retry lookup without dict_ton_bas when no match.
    if not choices:
        legacy_tokens = clean_text(text, apply_ton_bas=False).split()
        if legacy_tokens != tokens:
            choices, used_context = _interpolate_ngram_choices(
                model, legacy_tokens, context_length
            )

    # "pen" ↔ "pèn", "la'" ↔ "là'": if user omits tone, assume low (ton bas) for lookup.
    if not choices:
        assumed_tokens, changed = _tokens_assume_low_tone_bare_vowels(tokens)
        if changed:
            choices, used_context = _interpolate_ngram_choices(
                model, assumed_tokens, context_length
            )

    if not choices:
        return {
            "normalized_text": normalized_text,
            "used_context": 0,
            "suggestions": [],
        }

    ranked = sorted(
        (
            {"word": word, "probability": probability}
            for word, probability in choices.items()
            if word is not None
        ),
        key=lambda item: (
            item["probability"],
            _word_nufi_display_priority(item["word"]),
        ),
        reverse=True,
    )

    # Model keys may still use legacy tone marks; align display with clean_text / ton_bas.
    for item in ranked:
        item["word"] = clean_text(item["word"])

    # Older pickles or merged n-grams can keep two keys (e.g. "lah" and "làh") that collapse
    # to the same display form — merge probabilities so the UI does not show duplicates.
    merged = {}
    for item in ranked:
        w = item["word"]
        if w not in merged:
            merged[w] = {"word": w, "probability": item["probability"]}
        else:
            merged[w]["probability"] += item["probability"]

    # Old pickles may still map ("n",) -> b with probability 1.0 from Latin "N. B." lines
    # (see _strip_nota_bene_markers). Drop that lone spurious continuation at inference.
    if (
        len(tokens) == 1
        and tokens[0] == "n"
        and len(merged) == 1
        and "b" in merged
    ):
        merged.pop("b", None)

    ranked = sorted(
        merged.values(),
        key=lambda item: (
            item["probability"],
            _word_nufi_display_priority(item["word"]),
        ),
        reverse=True,
    )

    return {
        "normalized_text": normalized_text,
        "used_context": used_context or 0,
        "suggestions": ranked[: max(1, int(limit))],
    }


def generate_text_from_model(model, text, n=DEFAULT_ORDER):
    return generate_text_details(model, text, n=n)["result"]
