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
