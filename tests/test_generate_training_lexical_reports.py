from scripts import generate_training_lexical_reports as reports


def test_iter_filtered_tokens_skips_numeric_and_pointer_tokens(monkeypatch):
    monkeypatch.setattr(
        reports.nm,
        "load_corpus_bundle",
        lambda base_dir: {
            "cleaned": [],
            "tokens": [],
            "sentence_sources": {
                "001 --> 002": [{"path": "a.txt", "type": "txt", "reference": "line 1"}],
                "10 djeuleu": [{"path": "b.txt", "type": "txt", "reference": "line 2"}],
                "mɑ́ kɑ́ lī": [{"path": "c.txt", "type": "txt", "reference": "line 3"}],
                "ntúmbō 1964": [{"path": "d.txt", "type": "txt", "reference": "line 4"}],
            },
        },
    )

    tokens = reports._iter_filtered_tokens()

    assert "001" not in tokens
    assert "-->" not in tokens
    assert "1964" not in tokens
    assert "10" not in tokens
    assert "djeuleu" in tokens
    assert "mɑ́" in tokens
    assert "ntúmbō" in tokens


def test_is_alpha_word_token():
    assert reports._is_alpha_word_token("mɑ́") is True
    assert reports._is_alpha_word_token("ngǔ'") is True
    assert reports._is_alpha_word_token("11") is False
    assert reports._is_alpha_word_token("11)") is False
    assert reports._is_alpha_word_token("co") is True


def test_count_unicode_letters_ignores_combining_marks():
    assert reports.count_unicode_letters("mɑ́") == 2
    assert reports.count_unicode_letters("ntúmbō") == 6
    assert reports.count_unicode_letters("ngǔ'") == 3


def test_frequent_alpha_words_by_min_letters():
    from collections import Counter

    alpha_counts = Counter(
        {
            "mɑ́": 40,
            "kɑ́": 30,
            "ntúmbō": 25,
            "ngǔ'": 22,
            "co": 20,
            "lī": 15,
        }
    )

    payload = reports.frequent_alpha_words_by_min_letters(alpha_counts, min_letters=3, limit=100)

    assert payload["matching_unique_words"] == 2
    assert [item["word"] for item in payload["words"]] == ["ntúmbō", "ngǔ'"]
    assert payload["words"][0]["letter_count"] == 6
    assert payload["words"][1]["letter_count"] == 3
    assert all(item["letter_count"] >= 3 for item in payload["words"])
    assert "max_letters" not in payload


def test_frequent_alpha_words_by_min_and_max_letters():
    from collections import Counter

    alpha_counts = Counter(
        {
            "mɑ́": 40,
            "kɑ́": 30,
            "ntúmbō": 25,
            "ngǔ'": 22,
            "co": 20,
            "lī": 15,
        }
    )

    payload = reports.frequent_alpha_words_by_min_letters(
        alpha_counts,
        min_letters=3,
        max_letters=4,
        limit=100,
    )

    assert payload["max_letters"] == 4
    assert payload["matching_unique_words"] == 1
    assert [item["word"] for item in payload["words"]] == ["ngǔ'"]
    assert payload["words"][0]["letter_count"] == 3


def test_iter_filtered_tokens_uses_rhs_of_assignment_lines():
    sentence_sources = {
        "almk = ǎ lén mɑ́ kɑ́": [{"path": "a.txt", "type": "txt", "reference": "line 1"}],
    }

    tokens = reports._iter_filtered_tokens_from_sentence_sources(sentence_sources)

    assert "almk" not in tokens
    assert tokens == ["ǎ", "lén", "mɑ́", "kɑ́"]


def test_iter_filtered_tokens_excludes_known_non_nufi_words():
    sentence_sources = {
        "amsconse balafon bibiane ceintre mɑ́": [{"path": "a.txt", "type": "txt", "reference": "line 1"}],
        "chuengoue jeremie kɑ́": [{"path": "b.txt", "type": "txt", "reference": "line 2"}],
    }

    tokens = reports._iter_filtered_tokens_from_sentence_sources(sentence_sources)

    assert "amsconse" not in tokens
    assert "balafon" not in tokens
    assert "bibiane" not in tokens
    assert "ceintre" not in tokens
    assert "chuengoue" not in tokens
    assert "jeremie" not in tokens
    assert "mɑ́" in tokens
    assert "kɑ́" in tokens
