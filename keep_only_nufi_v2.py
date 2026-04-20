import argparse
import csv
import sys
import unicodedata
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Dict, Iterable, List

from nltk.stem.snowball import SnowballStemmer
from nufi_bana_classification import normalize_bana_to_standard, normalize_ton_bas
from nufi_bana_standard_maps import dict_ton_bas
from wordfreq import top_n_list, zipf_frequency


ENGLISH = "English"
FRENCH = "French"
ENGLISH_FRENCH = "English/French"
NUFI = "Nufi"
OTHER = "Other"
PUNCT = "PUNCT"

EDGE_QUOTES = "'\"\u2018\u2019\u0060\u00b4\u02bc\u00ab\u00bb"
APOSTROPHES = {"'", "\u2019", "\u02bc"}
NUFI_BASE_CHARS = set("\u0251\u0254\u0259\u025b\u0289\u014b\u0186\u0190\u018f")
PROTECTED_NUFI_TOKENS = {
    "a",
    "fa'á",
    "n",
    "o",
    "pen",
    "po",
    "soh",
    "tua",
}
FRENCH_HINT_CHARS = set("çéèêëîïôœùûüÿæ")
FRENCH_HINT_SUFFIXES = (
    "tion",
    "tions",
    "ment",
    "ments",
    "euse",
    "euses",
    "eur",
    "eurs",
    "ique",
    "iques",
    "aire",
    "aires",
    "isme",
    "ismes",
    "iste",
    "istes",
    "ifié",
    "ifiés",
    "ifée",
    "ifées",
    "irent",
    "èrent",
)
FRENCH_DERIVATIONAL_SUFFIXES = (
    "onne",
    "onnes",
    "onne",
    "onnes",
    "ette",
    "ettes",
    "euse",
    "euses",
    "eur",
    "eurs",
    "ière",
    "ières",
    "ier",
    "iers",
)
FRENCH_APOSTROPHE_PREFIXES = {"c", "d", "j", "l", "m", "n", "qu", "s", "t"}
FRENCH_VERB_FORM_SUFFIXES = (
    "irent",
    "erent",
    "urent",
    "aient",
    "ions",
    "iez",
    "erai",
    "eras",
    "erez",
    "irai",
    "iras",
    "irez",
    "rai",
    "ras",
    "rez",
    "erait",
    "erais",
    "erons",
    "eront",
    "eriez",
    "erons",
    "eriez",
    "erons",
    "erons",
    "er",
    "ait",
    "ais",
    "ant",
    "ent",
    "ons",
    "ez",
    "it",
    "is",
    "it",
    "a",
)
FRENCH_VERB_SPECIAL_FORMS = {
    "va",
    "vais",
    "vas",
    "vont",
    "allait",
    "allaient",
    "boit",
    "boitait",
    "boivent",
    "fut",
    "furent",
}

FRENCH_STOPWORDS = {
    "a",
    "ai",
    "au",
    "aux",
    "avec",
    "ce",
    "ces",
    "comme",
    "dans",
    "de",
    "des",
    "du",
    "elle",
    "en",
    "est",
    "et",
    "il",
    "je",
    "la",
    "le",
    "les",
    "ma",
    "mais",
    "mes",
    "mon",
    "ne",
    "nous",
    "ou",
    "pas",
    "pour",
    "qu",
    "que",
    "qui",
    "sa",
    "se",
    "ses",
    "son",
    "sur",
    "ta",
    "te",
    "tes",
    "toi",
    "ton",
    "tu",
    "un",
    "une",
    "vous",
}

ENGLISH_STOPWORDS = {
    "a",
    "am",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "do",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "him",
    "how",
    "i",
    "in",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "she",
    "that",
    "the",
    "their",
    "there",
    "they",
    "this",
    "to",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "who",
    "why",
    "will",
    "with",
    "you",
    "your",
}


@dataclass(frozen=True)
class TokenLabel:
    token: str
    normalized: str
    label: str


@dataclass(frozen=True)
class Span:
    language: str
    text: str


def repair_mojibake(text: str) -> str:
    if not text:
        return text

    suspicious = ("\u00c3", "\u00c2", "\u00e2", "\u00cc", "\u00c9", "\u00f0")
    if not any(ch in text for ch in suspicious):
        return text

    try:
        return text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def normalize_text(text: str) -> str:
    text = repair_mojibake(text or "")
    text = text.replace("\ufeff", "")
    text = (
        text.replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u0060", "'")
        .replace("\u00b4", "'")
        .replace("\u02bc", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u00ab", '"')
        .replace("\u00bb", '"')
    )
    return unicodedata.normalize("NFC", text)


def normalize_token(token: str) -> str:
    return normalize_text(token).lower().strip()


def _build_bare_vowel_to_low_tone() -> dict[str, str]:
    out: dict[str, str] = {}
    vowel_bases = set("aeiouAEIOU\u0251\u0254\u0259\u025b\u0289\u0186\u0190\u018f")
    for low_tone, base in dict_ton_bas.items():
        low = unicodedata.normalize("NFC", low_tone)
        bare = unicodedata.normalize("NFC", base)
        if len(bare) != 1 or len(low) != 1:
            continue
        if bare not in vowel_bases:
            continue
        if bare not in out:
            out[bare] = low
        if bare.lower() not in out:
            out[bare.lower()] = low.lower()
    return out


BARE_VOWEL_TO_LOW_TONE = _build_bare_vowel_to_low_tone()


def has_tone_or_diacritic(text: str) -> bool:
    for char in text:
        if unicodedata.category(char) == "Mn":
            return True
        name = unicodedata.name(char, "")
        if any(
            marker in name
            for marker in (
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


def assume_low_tone_word(word: str) -> str:
    if not word or has_tone_or_diacritic(word):
        return word

    chars: list[str] = []
    changed = False
    for char in unicodedata.normalize("NFC", word):
        replacement = BARE_VOWEL_TO_LOW_TONE.get(char, char)
        if replacement != char:
            changed = True
        chars.append(replacement)

    return "".join(chars) if changed else word


def rebuild_text(tokens: List[str]) -> str:
    text = ""
    no_space_before = {".", ",", "!", "?", ";", ":", ")", "]", "}"}
    no_space_after = {"(", "[", "{", '"'}

    for token in tokens:
        if not text:
            text = token
        elif token in no_space_before:
            text += token
        elif text[-1] in no_space_after:
            text += token
        else:
            text += f" {token}"

    return text.strip()


def apply_low_tone_assumption(text: str) -> str:
    tokens = tokenize(text)
    assumed_tokens: List[str] = []

    for token in tokens:
        if is_punctuation(token):
            assumed_tokens.append(token)
        else:
            assumed_tokens.append(assume_low_tone_word(token))

    return rebuild_text(assumed_tokens)


def cleanup_nufi_tokens(tokens: List[str]) -> List[str]:
    cleaned: List[str] = []
    index = 0

    while index < len(tokens):
        token = tokens[index]
        if is_punctuation(token):
            cleaned.append(token)
            index += 1
            continue

        normalized = strip_edge_quotes(normalize_token(token))

        run_end = index + 1
        while run_end < len(tokens):
            next_token = tokens[run_end]
            if is_punctuation(next_token):
                break
            if strip_edge_quotes(normalize_token(next_token)) != normalized:
                break
            run_end += 1

        cleaned.append(token)
        index = run_end

    return cleaned


def cleanup_nufi_output(text: str) -> str:
    if not text:
        return text

    tokens = tokenize(text)
    tokens = cleanup_nufi_tokens(tokens)
    return rebuild_text(tokens)


def normalize_nufi_text(text: str) -> str:
    text = normalize_text(text)
    text = apply_low_tone_assumption(text)
    text = normalize_bana_to_standard(text)
    text = normalize_ton_bas(text)
    return unicodedata.normalize("NFC", text)


def normalize_nufi_token(token: str) -> str:
    return normalize_nufi_text(token).lower().strip()


def strip_edge_quotes(token: str) -> str:
    # Preserve apostrophe-like characters at token edges (they may represent glottal stops).
    if not token:
        return token
    # Remove only quote/guillemet characters, but keep apostrophes (ASCII and modifier)
    quote_chars = ''.join(ch for ch in EDGE_QUOTES if ch not in APOSTROPHES)
    return token.strip(quote_chars)


def _is_mark(char: str) -> bool:
    return unicodedata.category(char).startswith("M")


def _is_word_char(char: str) -> bool:
    category = unicodedata.category(char)
    return category[0] in {"L", "N"} or _is_mark(char) or char in APOSTROPHES


def _is_punct_symbol(char: str) -> bool:
    return unicodedata.category(char)[0] in {"P", "S"} and char not in APOSTROPHES


def tokenize(text: str) -> List[str]:
    text = normalize_text(text)
    tokens: List[str] = []
    current: List[str] = []

    for char in text:
        if _is_word_char(char):
            current.append(char)
            continue

        if current:
            tokens.append("".join(current))
            current = []

        if not char.isspace():
            tokens.append(char)

    if current:
        tokens.append("".join(current))

    return tokens


def is_punctuation(token: str) -> bool:
    return bool(token) and all(_is_punct_symbol(char) for char in token)


def _iter_lexicon_terms(raw_value: str) -> Iterable[str]:
    cleaned = strip_edge_quotes(normalize_token(raw_value))
    if not cleaned:
        return

    yield cleaned

    for piece in cleaned.split():
        piece = strip_edge_quotes(piece)
        if piece:
            yield piece


@lru_cache(maxsize=8)
def load_nufi_lexicon(csv_path: str | None = None) -> set[str]:
    path = Path(csv_path) if csv_path else Path(__file__).with_name("nufi_word_list.csv")
    lexicon: set[str] = set()

    with path.open(encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            raw_value = row.get("nufi_keyword") or row.get("audio_file") or ""
            if not raw_value and len(row) >= 3:
                raw_value = list(row.values())[2]

            for term in _iter_lexicon_terms(raw_value):
                lexicon.add(term)

    return lexicon


@lru_cache(maxsize=8192)
def foreign_scores(token: str) -> tuple[float, float]:
    return zipf_frequency(token, "en"), zipf_frequency(token, "fr")


class LanguageSegmenter:
    def __init__(
        self,
        lexicon_path: str | None = None,
        english_vocab_size: int = 100000,
        french_vocab_size: int = 100000,
        foreign_score_threshold: float = 3.2,
        decisive_margin: float = 0.55,
        english_wordlist_path: str | None = None,
    ):
        print("Loading Nufi lexicon...")
        self.nufi_lexicon = load_nufi_lexicon(lexicon_path)
        print("Loading English/French frequency dictionaries...")
        # Prefer a local strict English dictionary file if provided or present in cwd
        local_default = Path("tmp_v2_english_dictionary_strict_no_acronyms.txt")
        wordlist_path = Path(english_wordlist_path) if english_wordlist_path else (local_default if local_default.exists() else None)
        if wordlist_path and wordlist_path.exists():
            try:
                with wordlist_path.open(encoding="utf-8") as wf:
                    strict_set = {line.strip().lower() for line in wf if line.strip()}
                # keep a frequency-backed set to preserve prior heuristics, but prefer strict set for blacklist decisions
                freq_set = set(top_n_list("en", english_vocab_size))
                self.english_words = freq_set.union(strict_set)
                self.english_words_strict = strict_set
                print(f"Loaded local English wordlist: {wordlist_path} ({len(strict_set)} entries) + freq-backed ({len(freq_set)} entries)")
            except Exception:
                self.english_words = set(top_n_list("en", english_vocab_size))
                self.english_words_strict = set()
        else:
            self.english_words = set(top_n_list("en", english_vocab_size))
            self.english_words_strict = set()
        self.french_words = set(top_n_list("fr", french_vocab_size))
        self.french_stemmer = SnowballStemmer("french")
        self.french_stems = {self.french_stemmer.stem(word) for word in self.french_words if word.isalpha()}
        self.foreign_score_threshold = foreign_score_threshold
        self.decisive_margin = decisive_margin
        print(f"Loaded {len(self.nufi_lexicon)} Nufi lexicon entries")
        print(f"Loaded {len(self.english_words)} English words")
        print(f"Loaded {len(self.french_words)} French words")

    def segment_text(self, text: str) -> Dict:
        tokens = tokenize(text)
        labeled_tokens = self.label_tokens(tokens)
        spans = self.merge_spans(labeled_tokens)
        grouped = self.group_by_language(spans)

        return {
            "input_text": normalize_text(text),
            "tokens": [asdict(item) for item in labeled_tokens],
            "spans": [asdict(item) for item in spans],
            "grouped": grouped,
            "nufi_only": self.keep_only_nufi_from_spans(spans),
        }

    def keep_only_nufi_text(self, text: str) -> str:
        tokens = tokenize(text)
        labeled_tokens = self.label_tokens(tokens)
        spans = self.merge_spans(labeled_tokens)
        return self.keep_only_nufi_from_spans(spans)

    def label_tokens(self, tokens: List[str]) -> List[TokenLabel]:
        labeled: List[TokenLabel] = []

        for token in tokens:
            normalized = normalize_token(token)

            if is_punctuation(token):
                labeled.append(TokenLabel(token, normalized, PUNCT))
                continue

            label = self.classify_token(token, normalized)
            labeled.append(TokenLabel(token, normalized, label))

        return self._smooth_labels(labeled)

    def classify_token(self, token: str, normalized: str) -> str:
        apostrophe_french_label = self.french_apostrophe_label(normalized)
        if apostrophe_french_label:
            return apostrophe_french_label

        if "'" in normalized and normalized not in self.english_words and normalized not in self.french_words:
            return NUFI

        core = strip_edge_quotes(normalized)
        if not core:
            return OTHER

        if core in PROTECTED_NUFI_TOKENS:
            return NUFI

        if self.looks_like_nufi_word(core):
            return NUFI

        stopword_label = self.stopword_label(core)
        if stopword_label:
            return stopword_label

        french_verb_label = self.french_verb_label(core)
        if french_verb_label:
            return french_verb_label

        dictionary_label = self.dictionary_label(core)
        if dictionary_label:
            return dictionary_label

        english_score, french_score = foreign_scores(core)
        foreign_label = self.foreign_label(core, english_score, french_score)
        if foreign_label:
            return foreign_label

        french_hint_label = self.french_hint_label(core)
        if french_hint_label:
            return french_hint_label

        french_family_label = self.french_family_label(core)
        if french_family_label:
            return french_family_label

        assumed_core = assume_low_tone_word(core)
        if assumed_core != core and self.looks_like_nufi_word(assumed_core):
            return NUFI

        if self.is_unknown_titlecase_token(token):
            return OTHER

        return NUFI

    def stopword_label(self, token: str) -> str | None:
        in_en = token in ENGLISH_STOPWORDS
        in_fr = token in FRENCH_STOPWORDS

        if in_en and not in_fr:
            return ENGLISH
        if in_fr and not in_en:
            return FRENCH
        if in_en and in_fr:
            return ENGLISH_FRENCH
        return None

    def dictionary_label(self, token: str) -> str | None:
        in_en = token in self.english_words
        in_fr = token in self.french_words

        if in_en and not in_fr:
            return ENGLISH
        if in_fr and not in_en:
            return FRENCH
        if not in_en and not in_fr:
            return None

        assumed_token = assume_low_tone_word(token)
        if assumed_token != token and self.looks_like_nufi_word(assumed_token):
            return NUFI

        english_score, french_score = foreign_scores(token)
        if english_score - french_score >= self.decisive_margin:
            return ENGLISH
        if french_score - english_score >= self.decisive_margin:
            return FRENCH
        return ENGLISH_FRENCH

    def foreign_label(self, token: str, english_score: float, french_score: float) -> str | None:
        if max(english_score, french_score) < self.foreign_score_threshold:
            return None

        if english_score - french_score >= self.decisive_margin:
            return ENGLISH
        if french_score - english_score >= self.decisive_margin:
            return FRENCH

        if token.isascii() and max(english_score, french_score) >= 5.4:
            return ENGLISH_FRENCH

        return None

    def french_hint_label(self, token: str) -> str | None:
        if "'" in token:
            return None
        if any(char in NUFI_BASE_CHARS for char in token):
            return None
        if has_tone_or_diacritic(token):
            letter_count = sum(1 for char in token if unicodedata.category(char).startswith("L"))
            if letter_count <= 3:
                return None
        if any(char in FRENCH_HINT_CHARS for char in token):
            return FRENCH
        if token.endswith(FRENCH_HINT_SUFFIXES):
            return FRENCH
        return None

    def french_apostrophe_label(self, token: str) -> str | None:
        if "'" not in token:
            return None
        prefix, suffix = token.split("'", 1)
        if prefix not in FRENCH_APOSTROPHE_PREFIXES or not suffix:
            return None
        if suffix in self.french_words or suffix in FRENCH_STOPWORDS:
            return FRENCH
        if self.french_verb_label(suffix):
            return FRENCH
        if any(char in FRENCH_HINT_CHARS for char in suffix):
            return FRENCH
        if suffix.endswith(FRENCH_HINT_SUFFIXES):
            return FRENCH
        return None

    def french_verb_label(self, token: str) -> str | None:
        if "'" in token or not token.isascii():
            return None
        if token in PROTECTED_NUFI_TOKENS:
            return None
        if token in FRENCH_VERB_SPECIAL_FORMS:
            return FRENCH

        assumed_token = assume_low_tone_word(token)
        if assumed_token != token and self.looks_like_nufi_word(assumed_token):
            return None

        lemma_candidates = self.french_lemma_candidates(token)
        if any(candidate in self.french_words for candidate in lemma_candidates):
            return FRENCH

        token_stem = self.french_stemmer.stem(token)
        if token_stem in self.french_stems and token.endswith(FRENCH_VERB_FORM_SUFFIXES):
            return FRENCH

        english_score, french_score = foreign_scores(token)
        if token.endswith(FRENCH_VERB_FORM_SUFFIXES) and french_score >= 1.2 and french_score >= english_score:
            return FRENCH

        return None

    def french_lemma_candidates(self, token: str) -> set[str]:
        candidates: set[str] = set()

        def add_suffix_variants(stem: str, suffixes: tuple[str, ...]) -> None:
            if not stem:
                return
            for suffix in suffixes:
                candidates.add(stem + suffix)

        if token.endswith("irent"):
            add_suffix_variants(token[:-5], ("ir",))
        if token.endswith("erent"):
            add_suffix_variants(token[:-5], ("er",))
        if token.endswith("aient"):
            add_suffix_variants(token[:-5], ("er", "ir", "re", "oir"))
        if token.endswith(("ions", "iez")):
            add_suffix_variants(token[:-4], ("er", "ir", "re", "oir"))
        if token.endswith(("erai", "eras", "erez")):
            add_suffix_variants(token[:-4], ("er",))
        if token.endswith(("irai", "iras", "irez")):
            add_suffix_variants(token[:-4], ("ir",))
        if token.endswith(("ait", "ais", "ant", "ent", "ons", "ez", "it", "is")):
            stem = token[:-3] if token.endswith(("ait", "ais", "ant", "ent", "ons", "ez")) else token[:-2]
            add_suffix_variants(stem, ("er", "ir", "re", "oir"))
        if token.endswith("a"):
            add_suffix_variants(token[:-1], ("er",))

        return {candidate for candidate in candidates if candidate}

    def french_family_label(self, token: str) -> str | None:
        if "'" in token or not token.isascii():
            return None
        if token in PROTECTED_NUFI_TOKENS:
            return None

        for suffix in FRENCH_DERIVATIONAL_SUFFIXES:
            if not token.endswith(suffix):
                continue
            base = token[: -len(suffix)]
            if not base:
                continue
            candidates = {
                base,
                base + "e",
                base + "er",
                base + "ir",
                base + "on",
                base + "onne",
            }
            if any(candidate in self.french_words for candidate in candidates):
                return FRENCH

        return None

    def is_unknown_titlecase_token(self, token: str) -> bool:
        normalized_token = normalize_text(token)
        letters = [char for char in normalized_token if unicodedata.category(char).startswith("L")]
        if len(letters) < 2:
            return False
        if not letters[0].isupper():
            return False
        return all(char.islower() for char in letters[1:])

    def looks_like_nufi_word(self, token: str, canonical_token: str | None = None) -> bool:
        if token in self.nufi_lexicon:
            return True

        if canonical_token and canonical_token in self.nufi_lexicon:
            return True

        if any(char in NUFI_BASE_CHARS for char in token):
            return True

        if any(unicodedata.category(char) == "Mn" for char in token):
            return True

        for char in token:
            name = unicodedata.name(char, "")
            if "WITH CARON" in name or "WITH MACRON" in name:
                return True

        return False

    def _smooth_labels(self, labeled_tokens: List[TokenLabel]) -> List[TokenLabel]:
        smoothed = list(labeled_tokens)

        for index, item in enumerate(smoothed):
            if item.label != OTHER:
                continue

            core = strip_edge_quotes(item.normalized)
            if not core:
                continue

            english_score, french_score = foreign_scores(core)
            if max(english_score, french_score) >= self.foreign_score_threshold:
                continue

            left_label = self._neighbor_label(smoothed, index, -1)
            right_label = self._neighbor_label(smoothed, index, 1)
            should_promote = (left_label == NUFI or right_label == NUFI) and (
                any(ord(char) > 127 for char in core) or "'" in core
            )

            if should_promote:
                smoothed[index] = TokenLabel(item.token, item.normalized, NUFI)

        return smoothed

    def _neighbor_label(self, labeled_tokens: List[TokenLabel], start: int, step: int) -> str | None:
        index = start + step

        while 0 <= index < len(labeled_tokens):
            label = labeled_tokens[index].label
            if label != PUNCT:
                return label
            index += step

        return None

    def merge_spans(self, labeled_tokens: List[TokenLabel]) -> List[Span]:
        spans: List[Span] = []
        current_language: str | None = None
        current_tokens: List[str] = []

        for item in labeled_tokens:
            if item.label == PUNCT:
                if current_tokens:
                    current_tokens.append(item.token)
                continue

            if current_language is None:
                current_language = item.label
                current_tokens = [item.token]
                continue

            if item.label == current_language:
                current_tokens.append(item.token)
                continue

            spans.append(Span(current_language, self.rebuild(current_tokens)))
            current_language = item.label
            current_tokens = [item.token]

        if current_tokens and current_language is not None:
            spans.append(Span(current_language, self.rebuild(current_tokens)))

        return spans

    def rebuild(self, tokens: List[str]) -> str:
        text = ""
        no_space_before = {".", ",", "!", "?", ";", ":", ")", "]", "}"}
        no_space_after = {"(", "[", "{", '"'}

        for token in tokens:
            if not text:
                text = token
            elif token in no_space_before:
                text += token
            elif text[-1] in no_space_after:
                text += token
            else:
                text += f" {token}"

        return text.strip()

    def group_by_language(self, spans: List[Span]) -> Dict[str, List[str]]:
        grouped = {
            ENGLISH: [],
            FRENCH: [],
            ENGLISH_FRENCH: [],
            NUFI: [],
            OTHER: [],
        }

        for span in spans:
            grouped[span.language].append(span.text)

        return grouped

    def keep_only_nufi_from_spans(self, spans: List[Span]) -> str:
        raw_nufi_text = " ".join(span.text for span in spans if span.language == NUFI).strip()
        return cleanup_nufi_output(normalize_nufi_text(raw_nufi_text))


def process_stream(instream, outstream, segmenter: LanguageSegmenter) -> None:
    for line in instream:
        outstream.write(segmenter.keep_only_nufi_text(line.rstrip("\n")) + "\n")


def demo(segmenter: LanguageSegmenter) -> None:
    text = "Hello mon ami, \u01cd c\u00e1' kh\u00f9 \u0101, how are you?"
    result = segmenter.segment_text(text)

    print("\n===== RESULT =====\n")

    print("Tokens:")
    for token in result["tokens"]:
        print(f"{token['token']:15} -> {token['label']}")

    print("\nSpans:")
    for span in result["spans"]:
        print(f"{span['language']}: [{span['text']}]")

    print("\nGrouped:")
    for language, values in result["grouped"].items():
        print(f"{language}: {values}")

    print("\nNufi only:")
    print(result["nufi_only"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Extract Nufi spans from mixed-language text.")
    parser.add_argument("input_path", nargs="?", help="Optional input text file to process line by line.")
    parser.add_argument("--demo", action="store_true", help="Run a small mixed-language demo.")
    return parser


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    args = build_parser().parse_args(argv)
    segmenter = LanguageSegmenter()

    if args.demo or (args.input_path is None and sys.stdin.isatty()):
        demo(segmenter)
        return 0

    if args.input_path:
        with open(args.input_path, encoding="utf-8", errors="ignore") as input_file:
            process_stream(input_file, sys.stdout, segmenter)
        return 0

    process_stream(sys.stdin, sys.stdout, segmenter)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
