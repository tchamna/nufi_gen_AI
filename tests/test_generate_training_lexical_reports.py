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
    assert reports._is_alpha_word_token("ngǒ'") is True
    assert reports._is_alpha_word_token("11") is False
    assert reports._is_alpha_word_token("11)") is False
    assert reports._is_alpha_word_token("co") is True
